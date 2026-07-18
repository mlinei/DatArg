export const COLORS = ['#59a7ff', '#45d4ff', '#8b8cff', '#f6c85f', '#fb7185', '#b9e3ff', '#22d3ee'];

const regions = {
  total_31_agglomerates: 'Total 31 aglomerados', greater_buenos_aires: 'Gran Buenos Aires',
  pampean: 'Pampeana', northwest: 'Noroeste', northeast: 'Noreste', cuyo: 'Cuyo', patagonia: 'Patagonia'
};
const sectors = {
  agriculture_forestry: 'Agro y silvicultura', manufacturing: 'Industria manufacturera', construction: 'Construcción',
  wholesale_retail_repairs: 'Comercio', mining_quarrying: 'Minería', financial_intermediation: 'Intermediación financiera',
  transport_communications: 'Transporte y comunicaciones', electricity_gas_water: 'Electricidad, gas y agua',
  hotels_restaurants: 'Hoteles y restaurantes', fishing: 'Pesca', education: 'Enseñanza',
  health_social_services: 'Salud y servicios sociales', public_administration_defense: 'Administración pública',
  real_estate_business_rental: 'Inmobiliarias y empresariales', community_social_personal_services: 'Servicios comunitarios',
  taxes_net_subsidies: 'Impuestos netos de subsidios'
};
const industry = {
  total: 'Nivel general', food_beverages: 'Alimentos y bebidas', textiles: 'Textiles', apparel_leather_footwear: 'Indumentaria y cuero',
  wood_paper_printing: 'Madera, papel e impresión', petroleum_refining: 'Refinación de petróleo', chemicals: 'Químicos',
  rubber_plastic: 'Caucho y plástico', nonmetallic_minerals: 'Minerales no metálicos', basic_metals: 'Metales básicos',
  metal_products: 'Productos de metal', machinery_equipment: 'Maquinaria y equipo', motor_vehicles: 'Vehículos automotores',
  other_transport_equipment: 'Otro equipo de transporte', furniture_other_manufacturing: 'Muebles y otras',
  other_equipment_instruments: 'Otros equipos e instrumentos', tobacco: 'Tabaco'
};
const wages = {
  total: 'Total', total_registered: 'Total registrado', private_registered: 'Privado registrado',
  public: 'Sector público', private_unregistered: 'Privado no registrado'
};

export const sections = [
  {
    id: 'precios', eyebrow: 'PRECIOS', title: 'Inflación', intro: 'Evolución del IPC nacional y los precios mayoristas publicados por INDEC.', file: 'inflation.csv',
    charts: [
      { title: 'Inflación mensual', subtitle: 'Variación porcentual contra el mes anterior', unit: '%', defaultRange: '5Y', series: {
        indec_ipc_general_mom: 'Nivel general', indec_ipc_core_mom: 'Núcleo', indec_ipc_regulated_mom: 'Regulados', indec_ipc_seasonal_mom: 'Estacionales', indec_ipim_general_mom: 'Mayorista'
      }},
      { title: 'Inflación interanual', subtitle: 'Variación contra igual mes del año anterior', unit: '%', series: { indec_ipc_general_yoy: 'IPC general', indec_ipc_core_yoy: 'IPC núcleo' }}
    ]
  },
  {
    id: 'actividad', eyebrow: 'ACTIVIDAD', title: 'Actividad económica', intro: 'EMAE mensual y desempeño sectorial. Base 2004=100.', file: 'emae.csv',
    charts: [
      { title: 'EMAE', subtitle: 'Índice desestacionalizado y tendencia-ciclo', unit: 'índice', series: { indec_emae_sa_index: 'Desestacionalizado', indec_emae_trend_cycle_index: 'Tendencia-ciclo' }},
      { title: 'Crecimiento por sector', subtitle: 'Variación interanual; elegí un sector', unit: '%', selector: Object.fromEntries(Object.entries(sectors).map(([k,v]) => [`indec_emae_sector_${k}_yoy`,v])), selected: 'indec_emae_sector_manufacturing_yoy' }
    ]
  },
  {
    id: 'pbi', eyebrow: 'CUENTAS NACIONALES', title: 'Producto interno bruto', intro: 'PIB trimestral y anual a precios constantes de 2004.', file: 'gdp.csv',
    charts: [
      { title: 'Crecimiento del PIB', subtitle: 'Variación interanual trimestral', unit: '%', series: { indec_gdp_growth_quarterly: 'PIB trimestral' }},
      { title: 'PIB desestacionalizado', subtitle: 'Millones de pesos de 2004', unit: 'M ARS 2004', series: { indec_gdp_sa_constant_2004: 'PIB real desestacionalizado' }}
    ]
  },
  {
    id: 'industria', eyebrow: 'PRODUCCIÓN', title: 'Industria manufacturera', intro: 'IPI manufacturero general y por rama de actividad.', file: 'industry.csv',
    charts: [{ title: 'Producción industrial', subtitle: 'Compará el nivel de producción o su variación interanual', unit: 'índice', composite: {
      sectors: industry, metrics: { index: 'Nivel del índice', yoy: 'Variación interanual' }, defaultSector: 'total', defaultMetric: 'index'
    }}]
  },
  {
    id: 'trabajo', eyebrow: 'MERCADO LABORAL', title: 'Empleo y participación', intro: 'Tasas trimestrales de actividad, empleo y desocupación para 31 aglomerados urbanos.', file: 'labor.csv',
    charts: [{ title: 'Indicadores laborales', subtitle: 'Seleccioná total nacional o una región', unit: '%', regionSelector: regions, metrics: { activity: 'Actividad', employment: 'Empleo', unemployment: 'Desocupación' }, region: 'total_31_agglomerates' }]
  },
  {
    id: 'salarios', eyebrow: 'INGRESOS', title: 'Salarios', intro: 'Evolución mensual del índice de salarios del INDEC para el total y sus segmentos oficiales.', file: 'wages.csv',
    warning: 'El sector privado no registrado es una estimación basada en la EPH y no equivale a la totalidad del empleo informal. El salario real se calcula como índice salarial dividido por IPC nacional y se expresa con diciembre de 2016=100.',
    charts: [
      { title: 'Salarios nominales', subtitle: 'Índice oficial o cambio contra el mes anterior', unit: 'índice', metricToggle: { default: 'index', labels: { index: 'Nivel del índice', mom: 'Variación mensual' } }, series: Object.fromEntries(Object.entries(wages).map(([key, label]) => [`indec_wage_${key}_nominal_{metric}`, label])) },
      { title: 'Salarios reales', subtitle: 'Poder adquisitivo frente al IPC; nivel base diciembre de 2016=100', unit: 'índice real', metricToggle: { default: 'index', labels: { index: 'Nivel del índice', mom: 'Variación mensual' } }, series: Object.fromEntries(Object.entries(wages).map(([key, label]) => [`indec_wage_${key}_real_{metric}`, label])) }
    ]
  },
  {
    id: 'pobreza', eyebrow: 'CONDICIONES DE VIDA', title: 'Pobreza e indigencia', intro: 'Incidencia semestral sobre personas en los 31 aglomerados urbanos relevados por la EPH.', file: 'poverty.csv',
    charts: [{ title: 'Personas bajo la línea', subtitle: 'Seleccioná total nacional o una región', unit: '%', regionSelector: regions, metrics: { poverty: 'Pobreza', indigence: 'Indigencia' }, region: 'total_31_agglomerates' }]
  },
  {
    id: 'comercio', eyebrow: 'SECTOR EXTERNO', title: 'Comercio exterior', intro: 'Exportaciones, importaciones y saldo comercial mensual de bienes.', file: 'trade.csv',
    charts: [{ title: 'Intercambio comercial argentino', subtitle: 'Millones de dólares por mes', unit: 'USD M', series: { indec_trade_exports: 'Exportaciones', indec_trade_imports: 'Importaciones', indec_trade_balance: 'Saldo' }}]
  },
  {
    id: 'reservas', eyebrow: 'SECTOR EXTERNO', title: 'Reservas internacionales', intro: 'Stock diario de reservas internacionales brutas del Banco Central. Las cifras son provisorias y pueden cambiar por valuación.', file: 'reserves.csv',
    charts: [{ title: 'Reservas brutas del BCRA', subtitle: 'Millones de dólares; cifras oficiales provisorias', unit: 'USD M', defaultRange: '5Y', series: { bcra_gross_international_reserves: 'Reservas brutas' }}]
  },
  {
    id: 'reservas-netas', eyebrow: 'SECTOR EXTERNO', title: 'Reservas internacionales netas', intro: 'Reconstrucción diaria de los activos de reserva disponibles luego de descontar encajes, swap con China, obligaciones con organismos internacionales y repos a un año.', file: 'net_reserves.csv',
    warning: 'Serie calculada por DatArg, no publicada oficialmente por el BCRA. Combina datos diarios, semanales y mensuales; entre publicaciones se arrastra o estima el último componente disponible y luego se recalibra. Los cortes del 30/06/2026 y 17/07/2026 fueron contrastados con la estimación de Federico Machado.',
    charts: [
      { title: 'Reservas netas', subtitle: 'Millones de dólares; definición corriente de mercado', unit: 'USD M', series: { bcra_net_international_reserves: 'Reservas netas' }},
      { title: 'Deducciones de las reservas brutas', subtitle: 'Componentes descontados, en millones de dólares', unit: 'USD M', series: { bcra_reserve_requirements_fx: 'Encajes', bcra_china_swap: 'Swap China', bcra_international_organizations_liability: 'OOII', bcra_repos_up_to_one_year: 'Repos ≤ 1 año' }}
    ]
  },
  {
    id: 'dolar', eyebrow: 'MERCADO CAMBIARIO', title: 'Tipos de cambio', intro: 'Cotizaciones históricas de venta del dólar oficial, blue, MEP y contado con liquidación.', file: 'exchange_rates.csv',
    charts: [{ title: 'Dólar por mercado', subtitle: 'Pesos argentinos por dólar', unit: 'ARS/USD', defaultRange: '5Y', series: { argentinadatos_usd_official_retail_sell: 'Oficial', argentinadatos_usd_blue_sell: 'Blue', argentinadatos_usd_mep_sell: 'MEP', argentinadatos_usd_ccl_sell: 'CCL' }}]
  },
  {
    id: 'mercados', eyebrow: 'MERCADO DE CAPITALES', title: 'S&P Merval en dólares', intro: 'Evolución del principal índice accionario argentino convertido al dólar MEP.', file: 'markets.csv',
    warning: 'Cálculo de DatArg: cierre diario del S&P Merval en pesos dividido por la cotización de venta del dólar MEP. Es una reconstrucción informativa y no la serie oficial licenciada S&P MERVAL (MEP).',
    charts: [{ title: 'S&P Merval en dólar MEP', subtitle: 'Puntos de índice en dólares financieros', unit: 'puntos USD', defaultRange: '5Y', series: { datarg_sp_merval_mep_usd: 'Merval / MEP' }}]
  },
  {
    id: 'riesgo', eyebrow: 'RIESGO SOBERANO', title: 'Riesgo país', intro: 'Evolución diaria del indicador de riesgo soberano argentino.', file: 'country_risk.csv',
    charts: [{ title: 'Riesgo país', subtitle: 'Puntos básicos', unit: 'pb', defaultRange: '5Y', series: { argentinadatos_country_risk: 'Riesgo país' }}]
  },
  {
    id: 'tasas', eyebrow: 'SISTEMA FINANCIERO', title: 'Tasas de interés', intro: 'BADLAR y TAMAR de bancos privados publicadas por el BCRA.', file: 'interest_rates.csv',
    charts: [{ title: 'Tasas mayoristas', subtitle: 'Tasa nominal anual', unit: '% TNA', defaultRange: '5Y', series: { bcra_badlar_private_tna: 'BADLAR', bcra_tamar_private_tna: 'TAMAR' }}]
  },
  {
    id: 'deuda', eyebrow: 'FINANZAS PÚBLICAS', title: 'Deuda pública', intro: 'Dos magnitudes separadas: deuda bruta de la Administración Central y pasivos financieros seleccionados del BCRA.', file: 'public_debt.csv', warning: 'Las series no se suman ni equivalen a deuda neta consolidada. Los pasivos seleccionados del BCRA incluyen LEBAC, NOBAC y otras letras emitidas en pesos y moneda extranjera; LELIQ y NOTALIQ; pases pasivos en pesos; y pases pasivos o REPO en dólares con el exterior. Los componentes en pesos se convierten al dólar mayorista de cierre mensual.',
    charts: [
      { title: 'Deuda bruta del Tesoro', subtitle: 'Administración Central, millones de USD', unit: 'USD M', series: { mecon_gross_central_government_debt: 'Tesoro' }},
      { title: 'Pasivos seleccionados del BCRA', subtitle: 'Instrumentos remunerados convertidos a USD', unit: 'USD M', series: { bcra_interest_bearing_liabilities: 'BCRA' }}
    ]
  }
];
