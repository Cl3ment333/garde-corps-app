# dessin_pdf.py

from fpdf import FPDF
from typing import List, Dict, Any, Optional
import json
import collections
import re

# --- PALETTE DE COULEURS ---
COLORS = {
    "poteau": (217, 30, 24), "lisse": (26, 188, 156), "barreau": (52, 152, 219),
    "cote": (142, 68, 173), "texte_noir": (0, 0, 0), "liaison": (108, 117, 125),
    "platine": (44, 62, 80)
}

# --- CLASSE PDF PERSONNALISÉE ---
class PlanPDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.show_main_header = True

    def header(self):
        if self.show_main_header:
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, 'Plan de Fabrication - Garde-Corps', 0, 1, 'C')
            self.ln(5)
            self.show_main_header = False 

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

# --- FONCTION PRINCIPALE ---
def creer_plan_pdf(data: Dict[str, Any]):
    try:
        pdf = PlanPDF(orientation='L', unit='mm', format='A4')
        
        dessiner_page_1(pdf, data)
        
        grouped_morceaux = collections.defaultdict(list)
        for morceau in data['morceaux']:
            structure_key = json.dumps([(s.get('type'), s.get('longueur')) for s in morceau['structure']])
            grouped_morceaux[structure_key].append(morceau)
            
        for structure_key, morceaux_group in grouped_morceaux.items():
            dessiner_page_morceau(pdf, morceaux_group[0], data, len(morceaux_group))

        if data.get('platine_details'):
            dessiner_page_platine(pdf, data['platine_details'], data['poteau_dims'])
            
        filepath = "plan_garde_corps.pdf"
        pdf.output(filepath)
        return filepath
    except Exception as e:
        print(f"Erreur lors de la création du PDF : {e}")
        import traceback
        traceback.print_exc()
        return None

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

def draw_horizontal_dim(pdf: FPDF, x, y, width, text):
    pdf.set_draw_color(*COLORS["cote"])
    pdf.set_text_color(*COLORS["cote"])
    pdf.set_line_width(0.2)
    pdf.line(x, y, x, y - 3)
    pdf.line(x + width, y, x + width, y - 3)
    pdf.line(x, y - 1.5, x + width, y - 1.5)
    pdf.set_font('Arial', '', 8)
    pdf.text(x + width / 2 - pdf.get_string_width(str(text)) / 2, y - 4.5, str(text))

def draw_vertical_dim(pdf: FPDF, x, y, height, text, right_side=False):
    offset = -1 if not right_side else 1
    pdf.set_draw_color(*COLORS["cote"])
    pdf.set_text_color(*COLORS["cote"])
    pdf.set_line_width(0.2)
    pdf.line(x, y, x + 3 * offset, y)
    pdf.line(x, y - height, x + 3 * offset, y - height)
    pdf.line(x + 1.5 * offset, y, x + 1.5 * offset, y - height)
    pdf.set_font('Arial', '', 8)
    text_width = pdf.get_string_width(str(text))
    if not right_side:
        pdf.text(x - text_width - 1, y - height / 2 + 1.5, str(text))
    else:
        pdf.text(x + 4, y - height / 2 + 1.5, str(text))

def draw_annotation(pdf: FPDF, x, y, title, detail, color, align='L'):
    pdf.set_text_color(*color)
    detail_text = f" ({detail})" if detail else ""
    if align == 'L':
        pdf.set_font('Arial', 'B', 9)
        title_width = pdf.get_string_width(title)
        pdf.text(x, y, title)
        pdf.set_font('Arial', 'I', 9)
        pdf.text(x + title_width, y, detail_text)
    elif align == 'R':
        pdf.set_font('Arial', 'I', 9)
        detail_width = pdf.get_string_width(detail_text)
        pdf.text(x - detail_width, y, detail_text)
        pdf.set_font('Arial', 'B', 9)
        title_width = pdf.get_string_width(title)
        pdf.text(x - detail_width - title_width, y, title)

# --- DESSIN DES PAGES ---
def dessiner_page_1(pdf: FPDF, data: Dict[str, Any]):
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "1. Vue d'Ensemble", 0, 1, 'L')
    pdf.ln(2)

    total_project_length = sum(m['longueur_totale'] for m in data['morceaux'])
    if total_project_length > 0:
        margin = 20
        drawing_width = pdf.w - 2 * margin
        overview_height = 20
        scale = drawing_width / total_project_length
        
        start_x = margin
        start_y = pdf.get_y() + overview_height

        cursor_x = 0
        for morceau in data['morceaux']:
            structure_items = [item for item in morceau['structure'] if item.get('type') != 'rien']
            for item in structure_items:
                item_type = item['type']
                if item_type in ['poteau', 'liaison']:
                    epaisseur = get_deduction_dimension(data[f"{item_type}_dims"])
                    pdf.set_draw_color(*COLORS[item_type])
                    pdf.rect(start_x + cursor_x * scale, start_y - overview_height, epaisseur * scale, overview_height, 'D')
                    cursor_x += epaisseur
                elif item_type == 'section':
                    longueur_libre = morceau['sections_details'][0]['longueur_libre']
                    pdf.set_draw_color(*COLORS['lisse'])
                    pdf.rect(start_x + cursor_x * scale, start_y - overview_height, longueur_libre * scale, overview_height, 'D')
                    cursor_x += longueur_libre
        
        draw_horizontal_dim(pdf, start_x, start_y + 5, total_project_length * scale, f"Longueur Totale: {total_project_length} mm")
        pdf.ln(15)

    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '2. Nomenclature Globale', 0, 1, 'L')
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 9)
    pdf.set_fill_color(220, 220, 220)
    col_widths = [60, 80, 40, 60]
    headers = ['Element', 'Details', 'Quantite', 'Longueur Unitaire']
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 7, header, 1, 0, 'C', True)
    pdf.ln()
    pdf.set_font('Arial', '', 9)
    for item in data['nomenclature']:
        pdf.cell(col_widths[0], 6, item['item'], 1)
        pdf.cell(col_widths[1], 6, item['details'], 1)
        pdf.cell(col_widths[2], 6, str(item['quantite']), 1, 0, 'C')
        pdf.cell(col_widths[3], 6, f"{item['longueur_unitaire_mm']} mm", 1, 0, 'R')
        pdf.ln()

def dessiner_page_platine(pdf: FPDF, platine: Dict[str, Any], poteau_dims: str):
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Détail de la Platine de Fixation', 0, 1, 'L')
    pdf.ln(10)
    pdf.set_font('Arial', 'BU', 10)
    pdf.cell(0, 10, 'Vue de dessus', 0, 1, 'C')
    pdf.ln(5)
    p_l, p_w = platine['longueur'], platine['largeur']
    center_x, center_y = pdf.w / 2, 80
    pdf.set_draw_color(*COLORS['platine'])
    pdf.set_line_width(0.5)
    pdf.rect(center_x - p_l / 2, center_y - p_w / 2, p_l, p_w)
    po_l = get_thickness_dimension(poteau_dims)
    po_w = get_deduction_dimension(poteau_dims)
    pdf.set_draw_color(*COLORS['poteau'])
    pdf.set_line_width(0.3)
    pdf.rect(center_x - po_l / 2, center_y - po_w / 2, po_l, po_w)
    e_l, e_w = platine['entraxe_longueur'], platine['entraxe_largeur']
    trou_d = platine['diametre_trous']
    pdf.set_draw_color(0,0,0)
    pdf.set_line_width(0.2)
    coords = [(center_x - e_l / 2, center_y - e_w / 2), (center_x + e_l / 2, center_y - e_w / 2), (center_x - e_l / 2, center_y + e_w / 2), (center_x + e_l / 2, center_y + e_w / 2)]
    for x, y in coords:
        pdf.circle(x, y, trou_d / 2)
    draw_horizontal_dim(pdf, center_x - p_l / 2, center_y + p_w / 2 + 10, p_l, str(p_l))
    draw_horizontal_dim(pdf, center_x - e_l / 2, center_y + p_w / 2 + 20, e_l, f"Entraxe {e_l}")
    draw_vertical_dim(pdf, center_x - p_l / 2 - 10, center_y + p_w / 2, p_w, str(p_w))
    draw_vertical_dim(pdf, center_x - p_l / 2 - 20, center_y + e_w / 2, e_w, f"Entraxe {e_w}")
    pdf.set_y(pdf.h - 60)
    pdf.set_font('Arial', 'BU', 10)
    pdf.cell(0, 10, 'Vue de cote', 0, 1, 'C')
    pdf.ln(5)
    p_e = platine['epaisseur']
    pdf.set_draw_color(*COLORS['platine'])
    pdf.set_line_width(0.5)
    pdf.rect(center_x - p_l / 2, pdf.h - 40, p_l, p_e)
    draw_vertical_dim(pdf, center_x + p_l / 2 + 5, pdf.h - 40 + p_e, p_e, str(p_e), right_side=True)

def dessiner_page_morceau(pdf: FPDF, morceau: Dict[str, Any], all_data: Dict[str, Any], repetition: int):
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"Détail du Morceau (longueur {morceau['longueur_totale']} mm)", 0, 1, 'C')
    if repetition > 1:
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 10, f"Répété {repetition} fois", 0, 1, 'C')
    pdf.ln(30)
    margin = 40
    drawing_width = pdf.w - 2 * margin
    drawing_height = pdf.h - 2 * margin - 40
    hauteur_totale = all_data['hauteur_totale']
    scale = min(drawing_width / morceau['longueur_totale'], drawing_height / hauteur_totale) if morceau['longueur_totale'] > 0 else 0
    def transform(x, y):
        origine_x = (pdf.w - morceau['longueur_totale'] * scale) / 2
        origine_y = pdf.h - margin - (pdf.h - 2 * margin - hauteur_totale * scale) / 2
        return origine_x + x * scale, origine_y - y * scale
    pdf.set_line_width(0.3)
    cursor_x = 0.0
    structure_items = [item for item in morceau['structure'] if item.get('type') != 'rien']
    section_details_iterator = iter(morceau['sections_details'])
    dims_map_visuel = {"poteau": get_deduction_dimension(all_data['poteau_dims']), "liaison": get_deduction_dimension(all_data['liaison_dims']), "barreau": get_deduction_dimension(all_data['barreau_dims'])}
    dims_map_epaisseur = {"lissehaute": get_thickness_dimension(all_data['lissehaute_dims']), "lissebasse": get_thickness_dimension(all_data['lissebasse_dims'])}
    for item in structure_items:
        item_type = item['type']
        if item_type in ['poteau', 'liaison']:
            epaisseur_visuelle = dims_map_visuel.get(item_type, 0)
            pdf.set_draw_color(*COLORS[item_type])
            x_rect, y_rect = transform(cursor_x, all_data['hauteur_totale'])
            pdf.rect(x_rect, y_rect, epaisseur_visuelle * scale, all_data['hauteur_totale'] * scale, 'D')
            cursor_x += epaisseur_visuelle
        elif item_type == 'section':
            try:
                section_details = next(section_details_iterator)
            except StopIteration:
                continue
            longueur_libre = section_details['longueur_libre']
            lisse_haute_ep = dims_map_epaisseur['lissehaute']
            lisse_basse_ep = dims_map_epaisseur['lissebasse']
            pdf.set_draw_color(*COLORS["lisse"])
            x_lisse, y_lisse_h = transform(cursor_x, all_data['hauteur_totale'])
            pdf.rect(x_lisse, y_lisse_h, longueur_libre * scale, lisse_haute_ep * scale, 'D')
            _, y_lisse_b = transform(cursor_x, all_data['hauteur_lisse_basse'] + lisse_basse_ep)
            pdf.rect(x_lisse, y_lisse_b, longueur_libre * scale, lisse_basse_ep * scale, 'D')
            if all_data.get('remplissage_type') == 'barreaudage_horizontal':
                remplissage_details = all_data.get('remplissage_details')
                if remplissage_details and remplissage_details['nombre_barreaux'] > 0:
                    pdf.set_draw_color(*COLORS["barreau"])
                    barreau_ep_horizontal = get_thickness_dimension(all_data['barreau_dims'])
                    jeu_depart_v = remplissage_details['jeu_depart_mm']
                    espacement_v = remplissage_details['vide_entre_barreaux_mm']
                    for k in range(remplissage_details['nombre_barreaux']):
                        y_pos = all_data['hauteur_lisse_basse'] + lisse_basse_ep + jeu_depart_v + k * (barreau_ep_horizontal + espacement_v)
                        x_barreau, y_barreau = transform(cursor_x, y_pos + barreau_ep_horizontal)
                        pdf.rect(x_barreau, y_barreau, longueur_libre * scale, barreau_ep_horizontal * scale, 'D')
            else: 
                barreau_ep_visuel = dims_map_visuel.get('barreau', 0)
                barreau_ep_calcul = get_deduction_dimension(all_data['barreau_dims'])
                if section_details['nombre_barreaux'] > 0:
                    pdf.set_draw_color(*COLORS["barreau"])
                    jeu_depart = section_details['jeu_depart_mm']
                    espacement = section_details['vide_entre_barreaux_mm']
                    pos_premier_barreau = cursor_x + jeu_depart
                    for k in range(section_details['nombre_barreaux']):
                        pos_x = pos_premier_barreau + k * (espacement + barreau_ep_calcul)
                        x_barreau, y_barreau = transform(pos_x, all_data['hauteur_totale'] - lisse_haute_ep)
                        h = (all_data['hauteur_totale'] - all_data['hauteur_lisse_basse'] - lisse_haute_ep - lisse_basse_ep) * scale
                        w = barreau_ep_visuel * scale
                        pdf.rect(x_barreau, y_barreau, w, h, 'D')
            cursor_x += longueur_libre
    x_origine, y_origine_bas = transform(0, 0)
    draw_vertical_dim(pdf, x_origine - 5, y_origine_bas, hauteur_totale * scale, str(hauteur_totale))
    _, y_lisse_basse_pdf = transform(0, all_data['hauteur_lisse_basse'])
    draw_vertical_dim(pdf, x_origine - 15, y_origine_bas, y_origine_bas - y_lisse_basse_pdf, str(all_data['hauteur_lisse_basse']))
    draw_horizontal_dim(pdf, x_origine, y_origine_bas + 5, morceau['longueur_totale'] * scale, f"L. Totale: {morceau['longueur_totale']}")
    temp_cursor_x_cote = 0
    for item in morceau['structure']:
        if item['type'] == 'section':
            longueur_section = item['longueur']
            x_sec_start, _ = transform(temp_cursor_x_cote, 0)
            draw_horizontal_dim(pdf, x_sec_start, y_origine_bas + 15, longueur_section * scale, f"Section: {longueur_section}")
            temp_cursor_x_cote += longueur_section
    y_annot_base = 30
    decalage_annot = 15
    draw_annotation(pdf, decalage_annot, y_annot_base, "Poteau:", all_data['poteau_dims'], COLORS["poteau"], align='L')
    draw_annotation(pdf, decalage_annot, y_annot_base + 10, "Liaison:", all_data['liaison_dims'], COLORS["liaison"], align='L')
    draw_annotation(pdf, decalage_annot, y_annot_base + 20, "Barreau:", all_data['barreau_dims'], COLORS["barreau"], align='L')
    draw_annotation(pdf, pdf.w - decalage_annot, y_annot_base, "Lisse Haute:", all_data['lissehaute_dims'], COLORS["lisse"], align='R')
    draw_annotation(pdf, pdf.w - decalage_annot, y_annot_base + 10, "Lisse Basse:", all_data['lissebasse_dims'], COLORS["lisse"], align='R')
