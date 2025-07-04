# main.py

import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import re
import math

# On importe le module pour la clé API, mais on le rend optionnel
try:
    import google.generativeai as genai
except ImportError:
    genai = None

from dessin_pdf import creer_plan_pdf

# --- CONFIGURATION ---
app = FastAPI(title="API Garde-Corps v11.0 (Unified)", version="11.0.0")

# Configuration de l'API Gemini (si la clé est disponible)
if genai:
    try:
        api_key = os.getenv("MA_CLE_GEMINI")
        if api_key:
            genai.configure(api_key=api_key)
        else:
            print("Avertissement: MA_CLE_GEMINI n'est pas définie. L'assistant IA sera désactivé.")
            genai = None
    except Exception as e:
        print(f"Erreur de configuration de l'API Gemini: {e}")
        genai = None

# Configuration CORS pour le développement local
origins = ["http://127.0.0.1:5500", "http://localhost:5500", "null"]
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODÈLES DE DONNÉES ---

class StructureItem(BaseModel):
    type: str
    longueur: Optional[int] = None

class MorceauData(BaseModel):
    nombre_sections: int
    structure: List[StructureItem]

class PlatineDetails(BaseModel):
    longueur: float
    largeur: float
    epaisseur: float
    nombre_trous: int
    diametre_trous: float
    entraxe_longueur: float
    entraxe_largeur: float

class ProjectData(BaseModel):
    hauteur_totale: int; hauteur_lisse_basse: int
    poteau_dims: str; liaison_dims: str
    lissehaute_dims: str; lissebasse_dims: str
    barreau_dims: str; ecart_barreaux: int
    type_fixation: str
    remplissage_type: str
    platine_dimensions: Optional[str] = None
    platine_trous: Optional[str] = None
    platine_entraxes: Optional[str] = None
    nombre_morceaux: int; morceaux_identiques: str
    morceaux: List[MorceauData]

class NomenclatureItem(BaseModel):
    item: str; details: str; quantite: int; longueur_unitaire_mm: int

class SectionPlan(BaseModel):
    longueur_section: float
    longueur_libre: float
    nombre_barreaux: int
    vide_entre_barreaux_mm: float
    jeu_depart_mm: float

class MorceauPlan(BaseModel):
    id: int
    longueur_totale: float
    structure: List[StructureItem]
    sections_details: List[SectionPlan]

class RepartitionResult(BaseModel):
    nombre_barreaux: int
    vide_entre_barreaux_mm: float
    jeu_depart_mm: float

class FinalPlanData(BaseModel):
    description_projet: str
    nomenclature: List[NomenclatureItem]
    morceaux: List[MorceauPlan]
    hauteur_totale: int; hauteur_lisse_basse: int
    poteau_dims: str; liaison_dims: str
    lissehaute_dims: str; lissebasse_dims: str; barreau_dims: str
    platine_details: Optional[PlatineDetails] = None
    remplissage_type: str
    remplissage_details: Optional[RepartitionResult] = None

class DescriptionData(BaseModel):
    description: str

class ParsedFormData(BaseModel):
    nombre_morceaux: Optional[int] = None
    morceaux_identiques: Optional[str] = "non"
    hauteur_totale: Optional[int] = 1020
    hauteur_lisse_basse: Optional[int] = 100
    poteau_dims: Optional[str] = "40x40"
    liaison_dims: Optional[str] = "40x20"
    lissehaute_dims: Optional[str] = "40x40"
    lissebasse_dims: Optional[str] = "40x40"
    barreau_dims: Optional[str] = "20x20"
    ecart_barreaux: Optional[int] = 110
    morceaux: Optional[List[MorceauData]] = []

# --- PROMPT POUR L'ASSISTANT IA ---
PROMPT_TEXT_PARSER = """
Tu es un expert en métallerie. Analyse la description textuelle d'un projet de garde-corps et extrais les informations pour pré-remplir un formulaire.

Description du projet :
---
{user_text}
---

Tâche :
Extrais les informations et retourne-les dans un format JSON strict.
- Déduis le nombre de morceaux.
- Pour chaque morceau, décris sa structure en alternant jonctions ('poteau', 'liaison') et 'section'. Une section a une 'longueur'.
- Si une information n'est pas présente, utilise les valeurs par défaut ou omets-la.

Exemple de sortie JSON attendue :
```json
{{
  "nombre_morceaux": 2,
  "hauteur_totale": 1020,
  "poteau_dims": "40x40",
  "morceaux": [
    {{
      "nombre_sections": 1,
      "structure": [
        {{"type": "poteau"}},
        {{"type": "section", "longueur": 3000}},
        {{"type": "liaison"}}
      ]
    }},
    {{
      "nombre_sections": 1,
      "structure": [
        {{"type": "liaison"}},
        {{"type": "section", "longueur": 4000}},
        {{"type": "poteau"}}
      ]
    }}
  ]
}}
```

Produis uniquement le JSON.
"""

# --- FONCTIONS AUXILIAIRES ---
def get_deduction_dimension(dim_string: str) -> float:
    if not dim_string: return 0
    numbers = re.findall(r'(\d+\.?\d*)', dim_string)
    if len(numbers) >= 2: return float(numbers[1])
    elif len(numbers) == 1: return float(numbers[0])
    return 0

def get_thickness_dimension(dim_string: str) -> float:
    if not dim_string: return 0
    numbers = re.findall(r'(\d+\.?\d*)', dim_string)
    if len(numbers) > 0: return float(numbers[0])
    return 0

def calculate_repartition(longueur_libre: float, epaisseur_barreau: float, ecart_maximal: float) -> RepartitionResult:
    if longueur_libre <= 0 or epaisseur_barreau <= 0 or ecart_maximal <= 0:
        return RepartitionResult(nombre_barreaux=0, vide_entre_barreaux_mm=0, jeu_depart_mm=longueur_libre)
    nombre_blocs = longueur_libre / (epaisseur_barreau + ecart_maximal)
    nombre_barreaux = math.ceil(nombre_blocs - 1)
    if nombre_barreaux < 0: nombre_barreaux = 0
    nombre_espaces = nombre_barreaux + 1
    longueur_totale_barreaux = nombre_barreaux * epaisseur_barreau
    espacement_reel = (longueur_libre - longueur_totale_barreaux) / nombre_espaces
    if espacement_reel > (ecart_maximal + 1e-9):
        nombre_barreaux += 1
        nombre_espaces = nombre_barreaux + 1
        longueur_totale_barreaux = nombre_barreaux * epaisseur_barreau
        espacement_reel = (longueur_libre - longueur_totale_barreaux) / nombre_espaces
    if nombre_barreaux <= 0:
        return RepartitionResult(nombre_barreaux=0, vide_entre_barreaux_mm=0, jeu_depart_mm=longueur_libre)
    return RepartitionResult(nombre_barreaux=nombre_barreaux, vide_entre_barreaux_mm=espacement_reel, jeu_depart_mm=espacement_reel)

def parse_platine_data(platine_string: str) -> Optional[PlatineDetails]:
    if not platine_string: return None
    try:
        parts = {p.split(':')[0].strip().lower(): p.split(':')[1].strip() for p in platine_string.split('/') if ':' in p}
        dims_part = next((p.strip() for p in platine_string.split('/') if ':' not in p), "")
        dims = [float(d) for d in re.findall(r'(\d+\.?\d*)', dims_part)]
        trous = [float(t) for t in re.findall(r'(\d+\.?\d*)', parts.get('trous', ''))]
        entraxes = [float(e) for e in re.findall(r'(\d+\.?\d*)', parts.get('entraxes', ''))]
        return PlatineDetails(longueur=dims[0], largeur=dims[1], epaisseur=dims[2], nombre_trous=int(trous[0]), diametre_trous=trous[1], entraxe_longueur=entraxes[0], entraxe_largeur=entraxes[1])
    except (IndexError, ValueError, KeyError): return None

# --- ROUTES API ---

@app.post("/api/parse-text", response_model=ParsedFormData)
async def parse_text_to_form(data: DescriptionData):
    if not genai:
        raise HTTPException(status_code=503, detail="Le service d'analyse IA n'est pas configuré.")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = PROMPT_TEXT_PARSER.format(user_text=data.description)
        response = await model.generate_content_async(prompt)
        response_text = response.text.strip()
        json_match = re.search(r'```json\n({.*?})\n```', response_text, re.DOTALL)
        json_str = json_match.group(1) if json_match else response_text
        parsed_data = json.loads(json_str)
        return ParsedFormData(**parsed_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse du texte: {str(e)}")

@app.post("/api/process-data")
async def process_data(data: ProjectData):
    final_morceaux = []
    dims_map = {"poteau": get_deduction_dimension(data.poteau_dims), "liaison": get_deduction_dimension(data.liaison_dims), "rien": 0}
    barreau_epaisseur_deduction = get_deduction_dimension(data.barreau_dims)
    try:
        for i, morceau_data in enumerate(data.morceaux):
            sections_details = []
            structure_items = [item for item in morceau_data.structure if item.type != 'rien']
            section_indices = [idx for idx, item in enumerate(structure_items) if item.type == 'section']
            for sec_idx in section_indices:
                longueur_section = structure_items[sec_idx].longueur
                jonction_gauche = structure_items[sec_idx - 1]
                jonction_droite = structure_items[sec_idx + 1]
                is_extremite_gauche = (sec_idx == 1)
                is_extremite_droite = (sec_idx == len(structure_items) - 2)
                deduction_gauche = dims_map.get(jonction_gauche.type, 0) / (1 if is_extremite_gauche else 2)
                deduction_droite = dims_map.get(jonction_droite.type, 0) / (1 if is_extremite_droite else 2)
                longueur_libre = longueur_section - deduction_gauche - deduction_droite
                repartition = RepartitionResult(nombre_barreaux=0, vide_entre_barreaux_mm=0, jeu_depart_mm=0)
                if data.remplissage_type == 'barreaudage_vertical':
                    repartition = calculate_repartition(longueur_libre, barreau_epaisseur_deduction, data.ecart_barreaux)
                sections_details.append(SectionPlan(longueur_section=longueur_section, longueur_libre=longueur_libre, **repartition.model_dump()))
            final_morceaux.append(MorceauPlan(id=i, longueur_totale=sum(s.longueur for s in morceau_data.structure if s.type == 'section' and s.longueur is not None), structure=morceau_data.structure, sections_details=sections_details))
        
        nomenclature = []
        total_poteaux, total_liaisons = 0, 0
        for m in data.morceaux:
            for s_item in m.structure:
                if s_item.type == 'poteau': total_poteaux +=1
                elif s_item.type == 'liaison': total_liaisons +=1
        if total_poteaux > 0: nomenclature.append(NomenclatureItem(item="Poteaux", details=data.poteau_dims, quantite=total_poteaux, longueur_unitaire_mm=data.hauteur_totale))
        if total_liaisons > 0: nomenclature.append(NomenclatureItem(item="Liaisons", details=data.liaison_dims, quantite=total_liaisons, longueur_unitaire_mm=data.hauteur_totale))
        total_longueur_lisses = sum(s.longueur_libre for m in final_morceaux for s in m.sections_details)
        if total_longueur_lisses > 0:
            nomenclature.append(NomenclatureItem(item="Lisse Haute", details=data.lissehaute_dims, quantite=1, longueur_unitaire_mm=round(total_longueur_lisses)))
            nomenclature.append(NomenclatureItem(item="Lisse Basse", details=data.lissebasse_dims, quantite=1, longueur_unitaire_mm=round(total_longueur_lisses)))
        
        remplissage_details = None
        if data.remplissage_type == 'barreaudage_vertical':
            total_barreaux = sum(s.nombre_barreaux for m in final_morceaux for s in m.sections_details)
            if total_barreaux > 0:
                epaisseur_lisse_haute = get_thickness_dimension(data.lissehaute_dims)
                epaisseur_lisse_basse = get_thickness_dimension(data.lissebasse_dims)
                longueur_unitaire_barreau = data.hauteur_totale - data.hauteur_lisse_basse - epaisseur_lisse_haute - epaisseur_lisse_basse
                nomenclature.append(NomenclatureItem(item="Barreaux", details=data.barreau_dims, quantite=total_barreaux, longueur_unitaire_mm=round(longueur_unitaire_barreau)))
        elif data.remplissage_type == 'barreaudage_horizontal':
            hauteur_disponible = data.hauteur_totale - data.hauteur_lisse_basse - get_thickness_dimension(data.lissehaute_dims) - get_thickness_dimension(data.lissebasse_dims)
            epaisseur_barreau_horizontal = get_thickness_dimension(data.barreau_dims)
            remplissage_details = calculate_repartition(hauteur_disponible, epaisseur_barreau_horizontal, data.ecart_barreaux)
            barreaux_par_longueur = {}
            for m in final_morceaux:
                for s in m.sections_details:
                    longueur = round(s.longueur_libre)
                    if longueur > 0: barreaux_par_longueur[longueur] = barreaux_par_longueur.get(longueur, 0) + 1
            if remplissage_details and remplissage_details.nombre_barreaux > 0:
                for longueur, nb_sections in barreaux_par_longueur.items():
                    nomenclature.append(NomenclatureItem(item=f"Barreaux L={longueur}mm", details=data.barreau_dims, quantite=remplissage_details.nombre_barreaux * nb_sections, longueur_unitaire_mm=longueur))
        
        platine_details = None
        if data.type_fixation == 'platine' and data.platine_dimensions and data.platine_trous and data.platine_entraxes:
            full_platine_string = f"{data.platine_dimensions} / Trous:{data.platine_trous} / Entraxes:{data.platine_entraxes}"
            platine_details = parse_platine_data(full_platine_string)
        
        final_data = FinalPlanData(description_projet=f"Garde-corps détaillé en {data.nombre_morceaux} morceau(x).", nomenclature=nomenclature, morceaux=final_morceaux, hauteur_totale=data.hauteur_totale, hauteur_lisse_basse=data.hauteur_lisse_basse, poteau_dims=data.poteau_dims, liaison_dims=data.liaison_dims, lissehaute_dims=data.lissehaute_dims, lissebasse_dims=data.lissebasse_dims, barreau_dims=data.barreau_dims, platine_details=platine_details, remplissage_type=data.remplissage_type, remplissage_details=remplissage_details)
        return {"status": "success", "data": final_data.model_dump()}
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_detail = f"Erreur inattendue: {str(e)}"
        raise HTTPException(status_code=500, detail=error_detail)

@app.post("/api/draw-pdf")
async def draw_pdf_plan(data: FinalPlanData):
    try:
        filepath = creer_plan_pdf(data.model_dump())
        if filepath:
            return FileResponse(path=filepath, media_type='application/pdf', filename='plan_garde_corps.pdf')
        else:
            raise HTTPException(status_code=500, detail="La création du PDF a échoué.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du dessin: {str(e)}")

# --- SERVIR LE FRONTEND ---
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

@app.get("/")
async def read_root():
    """Sert la page d'accueil de l'application."""
    return FileResponse('frontend/index.html')
