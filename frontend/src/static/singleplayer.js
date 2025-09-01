import { createSession } from './utils.js';

const modalitaA = document.querySelector('.mode-a-button');

createSession(modalitaA, "single", 'judge');

const modalitaB = document.querySelector('.mode-b-button');

createSession(modalitaB, "single", 'player');