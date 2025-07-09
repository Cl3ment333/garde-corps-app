document.addEventListener('DOMContentLoaded', () => {
    // --- REFERENCES AUX ELEMENTS DU DOM ---
    const tabForm = document.getElementById('tab-form');
    const tabIa = document.getElementById('tab-ia');
    const contentForm = document.getElementById('content-form');
    const contentIa = document.getElementById('content-ia');
    const gardeCorpsForm = document.getElementById('gardeCorpsForm');
    const resultatSection = document.getElementById('resultat');
    
    const nombreMorceauxInput = document.getElementById('nombre_morceaux');
    const morceauxIdentiquesRadios = document.querySelectorAll('input[name="morceaux_identiques"]');
    const morceauxContainer = document.getElementById('morceaux_container');

    const iaForm = document.getElementById('iaForm');

    let dernierePropositionComplete = null;

    // --- GESTION DES ONGLETS ---
    function switchTab(tabToShow, tabToHide, contentToShow, contentToHide) {
        contentToShow.classList.remove('hidden');
        contentToHide.classList.add('hidden');
        tabToShow.classList.add('text-indigo-600', 'border-indigo-600');
        tabToShow.classList.remove('text-slate-500', 'hover:text-slate-700');
        tabToHide.classList.add('text-slate-500', 'hover:text-slate-700');
        tabToHide.classList.remove('text-indigo-600', 'border-indigo-600');
    }
    if (tabForm && tabIa && contentForm && contentIa) {
        tabForm.addEventListener('click', () => switchTab(tabForm, tabIa, contentForm, contentIa));
        tabIa.addEventListener('click', () => switchTab(tabIa, tabForm, contentIa, contentForm));
    }
    
    // --- AJOUT DES BOUTONS DE SAUVEGARDE/CHARGEMENT ---
    const ctaContainer = gardeCorpsForm.querySelector('.cta-container');
    if (ctaContainer) {
        const saveLoadContainer = document.createElement('div');
        saveLoadContainer.className = 'flex justify-center gap-4 mt-4';
        saveLoadContainer.innerHTML = `
            <button id="saveProjectBtn" type="button" class="px-4 py-2 text-sm font-medium text-white bg-gray-600 rounded-md hover:bg-gray-700">Sauvegarder le projet</button>
            <button id="loadProjectBtn" type="button" class="px-4 py-2 text-sm font-medium text-white bg-gray-600 rounded-md hover:bg-gray-700">Charger le dernier projet</button>
        `;
        // Insérer après le formulaire principal, mais avant la section des résultats
        gardeCorpsForm.appendChild(saveLoadContainer);

        const saveBtn = document.getElementById('saveProjectBtn');
        const loadBtn = document.getElementById('loadProjectBtn');

        // --- LOGIQUE DE SAUVEGARDE ET CHARGEMENT ---
        saveBtn.addEventListener('click', () => {
            const formData = new FormData(gardeCorpsForm);
            const data = Object.fromEntries(formData.entries());
            localStorage.setItem('gardeCorpsProject', JSON.stringify(data));
            alert('Projet sauvegardé !');
        });

        loadBtn.addEventListener('click', () => {
            const savedData = localStorage.getItem('gardeCorpsProject');
            if (savedData) {
                const data = JSON.parse(savedData);
                prefillForm(data);
                alert('Projet chargé !');
            } else {
                alert('Aucun projet sauvegardé trouvé.');
            }
        });
    }


    // --- LOGIQUE DU FORMULAIRE DYNAMIQUE ---
    function createJunctionSelector(name) {
        const select = document.createElement('select');
        select.name = name;
        select.className = 'w-full p-2 border border-slate-300 rounded-md bg-slate-50';
        select.innerHTML = `<option value="rien">Rien</option><option value="poteau" selected>Poteau</option><option value="liaison">Liaison</option>`;
        return select;
    }
    function createSectionInput(morceauIndex, sectionIndex) {
        const div = document.createElement('div');
        div.className = 'flex items-center gap-2';
        const label = document.createElement('label');
        label.textContent = `Long. Section ${sectionIndex + 1} (mm):`;
        label.className = 'text-sm text-slate-600';
        const input = document.createElement('input');
        input.type = 'number';
        input.name = `morceau_${morceauIndex}_section_longueur_${sectionIndex}`;
        input.className = 'w-full p-2 border border-slate-300 rounded-md';
        input.placeholder = 'Ex: 1500';
        input.required = true;
        input.min = 1;
        div.appendChild(label);
        div.appendChild(input);
        return div;
    }
    function createMorceauUI(morceauIndex, isIdenticalTemplate = false) {
        const fieldset = document.createElement('fieldset');
        fieldset.className = 'p-4 border border-slate-200 rounded-lg';
        const legend = document.createElement('legend');
        legend.className = 'text-lg font-semibold text-slate-700 px-2';
        legend.textContent = isIdenticalTemplate ? 'Détail du morceau type' : `Détail du Morceau ${morceauIndex + 1}`;
        const contentDiv = document.createElement('div');
        contentDiv.className = 'space-y-4';
        const sectionsCountDiv = document.createElement('div');
        sectionsCountDiv.innerHTML = `<label for="morceau_${morceauIndex}_nombre_sections" class="block text-sm font-medium text-slate-600 mb-1">Nombre de sections pour ce morceau</label><input type="number" id="morceau_${morceauIndex}_nombre_sections" name="morceau_${morceauIndex}_nombre_sections" value="1" min="1" required class="w-full p-2 border border-slate-300 rounded-md">`;
        const structureContainer = document.createElement('div');
        structureContainer.className = 'mt-4 p-4 bg-slate-50 rounded-md space-y-3';
        contentDiv.appendChild(sectionsCountDiv);
        contentDiv.appendChild(structureContainer);
        fieldset.appendChild(legend);
        fieldset.appendChild(contentDiv);
        const sectionsCountInput = sectionsCountDiv.querySelector('input');
        sectionsCountInput.addEventListener('input', () => {
            renderStructure(morceauIndex, structureContainer, parseInt(sectionsCountInput.value, 10));
        });
        renderStructure(morceauIndex, structureContainer, parseInt(sectionsCountInput.value, 10));
        return fieldset;
    }
    function renderStructure(morceauIndex, container, count) {
        container.innerHTML = '';
        if (isNaN(count) || count < 1) return;
        const grid = document.createElement('div');
        grid.className = 'grid grid-cols-1 md:grid-cols-2 gap-4 items-end';
        const startDiv = document.createElement('div');
        startDiv.innerHTML = '<label class="text-sm font-medium text-slate-600">Début</label>';
        startDiv.appendChild(createJunctionSelector(`morceau_${morceauIndex}_jonction_0`));
        grid.appendChild(startDiv);
        for (let i = 0; i < count; i++) {
            grid.appendChild(createSectionInput(morceauIndex, i));
            const junctionDiv = document.createElement('div');
            junctionDiv.innerHTML = `<label class="text-sm font-medium text-slate-600">Jonction ${i + 1}</label>`;
            junctionDiv.appendChild(createJunctionSelector(`morceau_${morceauIndex}_jonction_${i + 1}`));
            grid.appendChild(junctionDiv);
        }
        container.appendChild(grid);
    }
    function renderForm() {
        morceauxContainer.innerHTML = '';
        const nbMorceaux = parseInt(nombreMorceauxInput.value, 10);
        const sontIdentiques = document.querySelector('input[name="morceaux_identiques"]:checked').value === 'oui';
        if (isNaN(nbMorceaux) || nbMorceaux < 1) return;
        if (sontIdentiques) {
            morceauxContainer.appendChild(createMorceauUI(0, true));
        } else {
            for (let i = 0; i < nbMorceaux; i++) {
                morceauxContainer.appendChild(createMorceauUI(i, false));
            }
        }
    }

    // --- EVENT LISTENERS ---
    nombreMorceauxInput.addEventListener('input', renderForm);
    morceauxIdentiquesRadios.forEach(radio => radio.addEventListener('change', renderForm));

    gardeCorpsForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        if (!gardeCorpsForm.checkValidity()) {
            gardeCorpsForm.reportValidity();
            return;
        }
        resultatSection.innerHTML = `<div class="p-4 text-center bg-blue-100 text-blue-800 rounded-lg"><p class="font-semibold">Calcul en cours...</p></div>`;
        const formData = new FormData(gardeCorpsForm);
        const data = Object.fromEntries(formData.entries());
        const projectData = { ...data, morceaux: [] };
        const nbMorceaux = parseInt(data.nombre_morceaux, 10);
        const sontIdentiques = data.morceaux_identiques === 'oui';
        const templateMorceau = {};
        if (sontIdentiques) {
            const nbSections = parseInt(data.morceau_0_nombre_sections, 10);
            templateMorceau.nombre_sections = nbSections;
            templateMorceau.structure = [];
            for (let i = 0; i <= nbSections; i++) {
                templateMorceau.structure.push({ type: data[`morceau_0_jonction_${i}`] });
                if (i < nbSections) {
                    templateMorceau.structure.push({ type: 'section', longueur: parseInt(data[`morceau_0_section_longueur_${i}`], 10) });
                }
            }
        }
        for (let i = 0; i < nbMorceaux; i++) {
            if (sontIdentiques) {
                projectData.morceaux.push(templateMorceau);
            } else {
                const morceau = {};
                const nbSections = parseInt(data[`morceau_${i}_nombre_sections`], 10);
                morceau.nombre_sections = nbSections;
                morceau.structure = [];
                 for (let j = 0; j <= nbSections; j++) {
                    morceau.structure.push({ type: data[`morceau_${i}_jonction_${j}`] });
                    if (j < nbSections) {
                        morceau.structure.push({ type: 'section', longueur: parseInt(data[`morceau_${i}_section_longueur_${j}`], 10) });
                    }
                }
                projectData.morceaux.push(morceau);
            }
        }
        try {
            const response = await fetch('/api/process-data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(projectData),
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Erreur du serveur.');
            }
            const result = await response.json();
            dernierePropositionComplete = result.data;
            displayResults(result.data);
        } catch (error) {
            resultatSection.innerHTML = `<div class="p-4 text-center bg-red-100 text-red-800 rounded-lg"><p class="font-semibold">Erreur</p><p>${error.message}</p></div>`;
        }
    });

    if (iaForm) {
        const descriptionProjetInput = document.getElementById('descriptionProjet');
        const iaSubmitButton = iaForm.querySelector('button[type="submit"]');

        iaForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const description = descriptionProjetInput.value;
            if (!description.trim()) {
                alert('Veuillez entrer une description.');
                return;
            }

            const originalButtonText = iaSubmitButton.innerHTML;
            iaSubmitButton.innerHTML = 'Analyse en cours...';
            iaSubmitButton.disabled = true;
            resultatSection.innerHTML = '';

            try {
                const response = await fetch('/api/parse-text', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ description: description }),
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || "L'analyse du texte a échoué.");
                }

                const parsedData = await response.json();
                prefillForm(parsedData);
                switchTab(tabForm, tabIa, contentForm, contentIa);

            } catch (error) {
                resultatSection.innerHTML = `<div class="p-4 text-center bg-red-100 text-red-800 rounded-lg"><p class="font-semibold">Erreur</p><p>${error.message}</p></div>`;
            } finally {
                iaSubmitButton.innerHTML = originalButtonText;
                iaSubmitButton.disabled = false;
            }
        });
    }

    function prefillForm(data) {
        for (const key in data) {
            if (data[key] !== null && key !== 'morceaux') {
                const input = gardeCorpsForm.querySelector(`[name="${key}"]`);
                if (input) {
                    if (input.type === 'radio') {
                        gardeCorpsForm.querySelector(`[name="${key}"][value="${data[key]}"]`).checked = true;
                    } else {
                        input.value = data[key];
                    }
                }
            }
        }
        
        const nbMorceaux = parseInt(data.nombre_morceaux, 10) || (data.morceaux ? data.morceaux.length : 1);
        nombreMorceauxInput.value = nbMorceaux;
        renderForm();

        if (data.morceaux && data.morceaux.length > 0) {
            data.morceaux.forEach((morceau, index) => {
                const nbSectionsInput = document.getElementById(`morceau_${index}_nombre_sections`);
                if (nbSectionsInput) {
                    nbSectionsInput.value = morceau.nombre_sections;
                    renderStructure(index, nbSectionsInput.closest('fieldset').querySelector('.mt-4'), morceau.nombre_sections);
                }
                if (morceau.structure) {
                    let sectionCursor = 0;
                    morceau.structure.forEach((item, structIndex) => {
                        if (item && item.type === 'section') {
                            const longueurInput = document.querySelector(`[name="morceau_${index}_section_longueur_${sectionCursor}"]`);
                            if (longueurInput) longueurInput.value = item.longueur;
                            const jonctionGauche = morceau.structure[structIndex - 1];
                            const jonctionInput = document.querySelector(`[name="morceau_${index}_jonction_${sectionCursor}"]`);
                            if(jonctionInput && jonctionGauche) jonctionInput.value = jonctionGauche.type;
                            const jonctionDroite = morceau.structure[structIndex + 1];
                            const jonctionInput2 = document.querySelector(`[name="morceau_${index}_jonction_${sectionCursor+1}"]`);
                            if(jonctionInput2 && jonctionDroite) jonctionInput2.value = jonctionDroite.type;
                            sectionCursor++;
                        } 
                    });
                }
            });
        } else {
            const sontIdentiques = data.morceaux_identiques === 'oui';
            const loopCount = sontIdentiques ? 1 : nbMorceaux;
            for(let i = 0; i < loopCount; i++) {
                const nbSections = parseInt(data[`morceau_${i}_nombre_sections`], 10);
                const nbSectionsInput = document.getElementById(`morceau_${i}_nombre_sections`);
                if(nbSectionsInput) {
                    nbSectionsInput.value = nbSections;
                    renderStructure(i, nbSectionsInput.closest('fieldset').querySelector('.mt-4'), nbSections);
                    for(let j = 0; j < nbSections; j++) {
                        document.querySelector(`[name="morceau_${i}_section_longueur_${j}"]`).value = data[`morceau_${i}_section_longueur_${j}`];
                        document.querySelector(`[name="morceau_${i}_jonction_${j}"]`).value = data[`morceau_${i}_jonction_${j}`];
                    }
                    document.querySelector(`[name="morceau_${i}_jonction_${nbSections}"]`).value = data[`morceau_${i}_jonction_${nbSections}`];
                }
            }
        }
    }

    function displayResults(data) {
        let nomenclatureHtml = '';
        if (data.nomenclature && data.nomenclature.length > 0) {
            const tableRows = data.nomenclature.map(item => `<tr class="border-b border-slate-200 last:border-b-0"><td class="p-3">${item.item}</td><td class="p-3 text-slate-600">${item.details}</td><td class="p-3 text-center">${item.quantite}</td><td class="p-3 text-right">${item.longueur_unitaire_mm} mm</td></tr>`).join('');
            nomenclatureHtml = `<div><h3 class="font-bold text-lg text-slate-700 mt-6 mb-2">Nomenclature</h3><div class="overflow-hidden border border-slate-200 rounded-lg"><table class="min-w-full bg-white text-sm"><thead class="bg-slate-50"><tr><th class="p-3 text-left font-semibold text-slate-600">Élément</th><th class="p-3 text-left font-semibold text-slate-600">Détails</th><th class="p-3 text-center font-semibold text-slate-600">Quantité</th><th class="p-3 text-right font-semibold text-slate-600">Longueur Unitaire</th></tr></thead><tbody>${tableRows}</tbody></table></div></div>`;
        }
        let planDetailsHtml = '';
        if (data.morceaux && data.morceaux.length > 0) {
            planDetailsHtml = data.morceaux.map((morceau, index) => {
                const sectionRows = morceau.sections_details.map((section, secIndex) => `<tr class="border-b border-slate-200 last:border-b-0"><td class="p-2 text-center">${secIndex + 1}</td><td class="p-2 text-right">${section.longueur_section.toFixed(1)} mm</td><td class="p-2 text-right">${section.longueur_libre.toFixed(1)} mm</td><td class="p-2 text-center">${section.nombre_barreaux}</td><td class="p-2 text-right">${section.vide_entre_barreaux_mm.toFixed(1)} mm</td><td class="p-2 text-right">${section.jeu_depart_mm.toFixed(1)} mm</td></tr>`).join('');
                return `<div class="mt-4"><h4 class="font-semibold text-md text-slate-700">Détail du Morceau ${index + 1} (Longueur totale: ${morceau.longueur_totale.toFixed(1)} mm)</h4><div class="overflow-hidden border border-slate-200 rounded-lg mt-1"><table class="min-w-full bg-white text-xs"><thead class="bg-slate-50"><tr><th class="p-2 text-center font-semibold text-slate-600">Section</th><th class="p-2 text-right font-semibold text-slate-600">Long. Section</th><th class="p-2 text-right font-semibold text-slate-600">Long. Libre</th><th class="p-2 text-center font-semibold text-slate-600">Nb. Barreaux</th><th class="p-2 text-right font-semibold text-slate-600">Vide entre Barreaux</th><th class="p-2 text-right font-semibold text-slate-600">Jeu Départ</th></tr></thead><tbody>${sectionRows}</tbody></table></div></div>`;
            }).join('');
        }
        resultatSection.innerHTML = `<div class="bg-white p-6 rounded-lg shadow-inner border border-slate-200 text-left space-y-4"><h2 class="text-2xl font-bold text-slate-800 border-b pb-2">Proposition Générée</h2><p class="text-slate-600">${data.description_projet || 'Description non fournie.'}</p>${nomenclatureHtml}<div><h3 class="font-bold text-lg text-slate-700 mt-6 mb-2">Plan de Fabrication Détaillé</h3>${planDetailsHtml}</div><div class="text-center pt-6"><button id="downloadPdfBtn" class="w-full bg-purple-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-purple-700 transition-colors">Télécharger le Plan PDF</button></div><div><h3 class="font-bold text-lg text-slate-700 mt-6 mb-2">Données Techniques (JSON)</h3><pre class="bg-slate-800 text-white p-4 rounded-md overflow-x-auto text-sm"><code>${JSON.stringify(data, null, 2)}</code></pre></div></div>`;
        document.getElementById('downloadPdfBtn').addEventListener('click', handleDownloadPdf);
    }
    async function handleDownloadPdf() {
        if (!dernierePropositionComplete) return;
        const downloadBtn = document.getElementById('downloadPdfBtn');
        downloadBtn.textContent = 'Génération en cours...';
        downloadBtn.disabled = true;
        try {
            const response = await fetch('/api/draw-pdf', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(dernierePropositionComplete),
            });
            if (!response.ok) {
                 const errorData = await response.json();
                throw new Error(errorData.detail || 'Erreur lors de la génération du PDF.');
            }
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'plan_garde_corps.pdf';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        } catch (error) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'p-4 mt-4 text-center bg-red-100 text-red-800 rounded-lg';
            errorDiv.innerHTML = `<p class="font-semibold">Erreur de téléchargement</p><p>${error.message}</p>`;
            resultatSection.appendChild(errorDiv);
        } finally {
            downloadBtn.textContent = 'Télécharger le Plan PDF';
            downloadBtn.disabled = false;
        }
    }
    
    renderForm();
});
