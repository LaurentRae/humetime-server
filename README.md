# Humetime Server

API FastAPI qui écrit dans un Google Sheet les informations dictées (patients, durée, repas, personnes…).

## Endpoints

### POST /append
Ajoute une ligne dans le Google Sheet.

Champs requis :
- nb_patients (int)
- duree_distribution_min (int)
- repas ("petit déjeuner" | "midi" | "soir", synonymes acceptés)
- nb_personnes (int)

Champs optionnels :
- horodatage (str)
- notes_libres (str)
- source_message (str)

## Déploiement sur Render

Build Command:
