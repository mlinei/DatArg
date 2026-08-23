export const AREAS = [
  {
    id: 'economia-real',
    eyebrow: 'Actividad y bienestar',
    title: 'Economía real',
    description: 'Precios, actividad, producción, empleo, ingresos y condiciones de vida.',
    sections: ['precios', 'actividad', 'pbi', 'consumo-privado', 'industria', 'trabajo', 'empleo-sector', 'empleo-provincia', 'salarios', 'pobreza'],
  },
  {
    id: 'bcra-financiero',
    eyebrow: 'Moneda y crédito',
    title: 'BCRA y sistema financiero',
    description: 'Reservas, intervención, depósitos, tasas, encajes y crédito bancario.',
    sections: ['reservas', 'reservas-netas', 'depositos-dolares', 'intervencion', 'agregados-monetarios', 'tasas', 'credito'],
  },
  {
    id: 'sector-externo',
    eyebrow: 'Dólar y activos',
    title: 'Sector externo y mercados',
    description: 'Comercio exterior, tipo de cambio, competitividad y mercados financieros.',
    sections: ['comercio', 'dolar', 'itcrm', 'mercados', 'riesgo', 'dividendos'],
  },
  {
    id: 'fiscal-deuda',
    eyebrow: 'Estado y financiamiento',
    title: 'Fiscal y deuda',
    description: 'Recaudación, resultado fiscal, inversión pública, liquidez, deuda y vencimientos.',
    sections: ['liquidez-tesoro', 'fiscal', 'gasto-publico', 'inversion-publica', 'prevision-social', 'fgs', 'deuda', 'vencimientos', 'deuda-neta'],
  },
];

export const areaForSection = sectionId => AREAS.find(area => area.sections.includes(sectionId));
