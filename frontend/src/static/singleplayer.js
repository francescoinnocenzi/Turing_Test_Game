import { createSession } from './utils.js';

// Seleziona i bottoni e crea le sessioni corrispondenti
const modalitaA = document.querySelector('.mode-a-button');

createSession(modalitaA, "single", 'judge');

const modalitaB = document.querySelector('.mode-b-button');

createSession(modalitaB, "single", 'player');