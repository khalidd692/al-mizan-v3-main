/**
 * Module de Confrontation - Timeline de la Science
 * Interface frontend pour afficher l'évolution des avis à travers les siècles
 */

class TimelineVisualization {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.currentHadithId = null;
        this.timelineData = null;
    }

    /**
     * Charge et affiche la timeline pour un hadith
     */
    async loadTimeline(hadithId) {
        this.currentHadithId = hadithId;
        
        try {
            const response = await fetch(`/api/timeline/${hadithId}`);
            this.timelineData = await response.json();
            this.render();
        } catch (error) {
            console.error('Erreur chargement timeline:', error);
            this.showError();
        }
    }

    /**
     * Rendu principal de la timeline
     */
    render() {
        if (!this.timelineData) return;

        const { hadith, timeline, consensus, divergences, metadata } = this.timelineData;

        this.container.innerHTML = `
            <div class="timeline-container">
                <!-- En-tête avec le hadith -->
                <div class="timeline-header">
                    <h2>📜 Chaîne de Transmission Scientifique</h2>
                    <div class="hadith-preview">
                        <p class="arabic">${hadith.arabic_text}</p>
                        <p class="translation">${hadith.french_translation || ''}</p>
                    </div>
                    <div class="consensus-badge ${consensus.exists ? 'consensus' : 'divergence'}">
                        ${consensus.interpretation} - ${consensus.percentage}%
                    </div>
                </div>

                <!-- Timeline par époques -->
                <div class="timeline-epochs">
                    ${this.renderEpoch('anciens', timeline.anciens, '🕌')}
                    ${this.renderEpoch('medievaux', timeline.medievaux, '📚')}
                    ${this.renderEpoch('contemporains', timeline.contemporains, '🎓')}
                </div>

                <!-- Analyse des divergences -->
                ${divergences.length > 0 ? this.renderDivergences(divergences) : ''}

                <!-- Métadonnées -->
                <div class="timeline-footer">
                    <p>✅ ${metadata.total_scholars} savants consultés</p>
                    <p>📅 Généré le ${new Date(metadata.generated_at).toLocaleString('fr-FR')}</p>
                </div>
            </div>
        `;

        this.attachEventListeners();
    }

    /**
     * Rendu d'une époque
     */
    renderEpoch(epochKey, scholars, icon) {
        if (!scholars || scholars.length === 0) {
            return `
                <div class="epoch-section empty">
                    <h3>${icon} ${this.getEpochName(epochKey)}</h3>
                    <p class="no-data">Aucun avis disponible pour cette période</p>
                </div>
            `;
        }

        return `
            <div class="epoch-section" data-epoch="${epochKey}">
                <h3>${icon} ${this.getEpochName(epochKey)}</h3>
                <p class="epoch-description">${this.getEpochDescription(epochKey)}</p>
                
                <div class="scholars-list">
                    ${scholars.map(s => this.renderScholar(s)).join('')}
                </div>
            </div>
        `;
    }

    /**
     * Rendu d'un savant
     */
    renderScholar(scholarData) {
        const { scholar, ruling } = scholarData;
        const gradeClass = this.getGradeClass(ruling.grade);

        return `
            <div class="scholar-card" data-scholar="${scholar.name}">
                <div class="scholar-header">
                    <h4>${scholar.name}</h4>
                    <span class="scholar-years">${scholar.years}</span>
                </div>
                
                <div class="scholar-info">
                    <span class="school">${scholar.school}</span>
                    <span class="specialization">${scholar.specialization}</span>
                    <span class="reliability">⭐ ${scholar.reliability}/10</span>
                </div>

                <div class="ruling ${gradeClass}">
                    <span class="grade-badge">${ruling.grade}</span>
                    <p class="reasoning">${ruling.reasoning || 'Pas de détails disponibles'}</p>
                </div>

                <button class="btn-scholar-profile" data-scholar="${scholar.name}">
                    Voir le profil complet
                </button>
            </div>
        `;
    }

    /**
     * Rendu des divergences
     */
    renderDivergences(divergences) {
        return `
            <div class="divergences-section">
                <h3>⚖️ Points de Divergence</h3>
                <div class="divergences-list">
                    ${divergences.map(d => `
                        <div class="divergence-item">
                            <h4>Position: ${d.position}</h4>
                            <p>Soutenue par ${d.count} savant(s):</p>
                            <ul>
                                ${d.scholars.map(s => `<li>${s}</li>`).join('')}
                            </ul>
                            ${d.main_reasoning ? `<p class="reasoning">${d.main_reasoning}</p>` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    /**
     * Utilitaires
     */
    getEpochName(epochKey) {
        const names = {
            'anciens': 'Les Anciens (Salaf)',
            'medievaux': 'Les Médiévaux',
            'contemporains': 'Les Contemporains'
        };
        return names[epochKey] || epochKey;
    }

    getEpochDescription(epochKey) {
        const descriptions = {
            'anciens': 'Les trois premières générations bénis (0-300H)',
            'medievaux': "L'âge d'or de la science du hadith (300-900H)",
            'contemporains': 'Les savants modernes (900H-présent)'
        };
        return descriptions[epochKey] || '';
    }

    getGradeClass(grade) {
        const gradeMap = {
            'Sahih': 'grade-sahih',
            'Hasan': 'grade-hasan',
            'Daif': 'grade-daif',
            'Mawdu': 'grade-mawdu'
        };
        return gradeMap[grade] || 'grade-unknown';
    }

    /**
     * Gestion des événements
     */
    attachEventListeners() {
        // Boutons profil savant
        this.container.querySelectorAll('.btn-scholar-profile').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const scholarName = e.target.dataset.scholar;
                this.showScholarProfile(scholarName);
            });
        });

        // Cartes savants (hover pour détails)
        this.container.querySelectorAll('.scholar-card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.classList.add('expanded');
            });
            card.addEventListener('mouseleave', () => {
                card.classList.remove('expanded');
            });
        });
    }

    /**
     * Affiche le profil complet d'un savant
     */
    async showScholarProfile(scholarName) {
        try {
            const response = await fetch(`/api/scholar/${encodeURIComponent(scholarName)}`);
            const profile = await response.json();
            
            // Créer une modale avec le profil
            const modal = document.createElement('div');
            modal.className = 'scholar-modal';
            modal.innerHTML = `
                <div class="modal-content">
                    <span class="close">&times;</span>
                    <h2>${profile.full_name}</h2>
                    <div class="profile-details">
                        <p><strong>Nom:</strong> ${profile.name}</p>
                        <p><strong>Années:</strong> ${profile.birth_year_hijri}-${profile.death_year_hijri}H</p>
                        <p><strong>École:</strong> ${profile.school}</p>
                        <p><strong>Spécialisation:</strong> ${profile.specialization}</p>
                        <p><strong>Fiabilité:</strong> ${profile.reliability_score}/10</p>
                        ${profile.biography ? `<p><strong>Biographie:</strong> ${profile.biography}</p>` : ''}
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // Fermeture modale
            modal.querySelector('.close').addEventListener('click', () => {
                modal.remove();
            });
            
        } catch (error) {
            console.error('Erreur chargement profil:', error);
        }
    }

    showError() {
        this.container.innerHTML = `
            <div class="timeline-error">
                <p>❌ Erreur lors du chargement de la timeline</p>
                <button onclick="location.reload()">Réessayer</button>
            </div>
        `;
    }
}

// Export pour utilisation
window.TimelineVisualization = TimelineVisualization;