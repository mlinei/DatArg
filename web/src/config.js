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
const registeredEmploymentSectors = {
  agriculture: 'Agricultura', fishing: 'Pesca', mining: 'Minería', manufacturing: 'Industria',
  utilities: 'Electricidad, gas y agua', construction: 'Construcción', commerce: 'Comercio',
  hotels_restaurants: 'Hoteles y restaurantes', transport_communications: 'Transporte y comunicaciones',
  finance: 'Intermediación financiera', business_services: 'Servicios empresariales', education: 'Enseñanza',
  health: 'Salud', community_services: 'Servicios comunitarios', unspecified: 'Sin especificar', total: 'Total'
};
const registeredEmploymentProvinces = {
  buenos_aires: 'Buenos Aires', caba: 'CABA', catamarca: 'Catamarca', chaco: 'Chaco', chubut: 'Chubut',
  cordoba: 'Córdoba', corrientes: 'Corrientes', entre_rios: 'Entre Ríos', formosa: 'Formosa', jujuy: 'Jujuy',
  la_pampa: 'La Pampa', la_rioja: 'La Rioja', mendoza: 'Mendoza', misiones: 'Misiones', neuquen: 'Neuquén',
  rio_negro: 'Río Negro', salta: 'Salta', san_juan: 'San Juan', san_luis: 'San Luis', santa_cruz: 'Santa Cruz',
  santa_fe: 'Santa Fe', santiago_del_estero: 'Santiago del Estero', tierra_del_fuego: 'Tierra del Fuego', tucuman: 'Tucumán'
};
const registeredEmploymentMetricToggle = (dimension, labels) => ({
  default: 'level',
  labels: { level: 'Puestos de trabajo', index: 'Índice ene-09=100', yoy: 'Variación interanual' },
  units: { level: 'miles de personas', index: 'índice', yoy: '%' },
  seriesByMetric: Object.fromEntries(['level', 'index', 'yoy'].map(metric => [metric,
    Object.fromEntries(Object.entries(labels).map(([slug, label]) => [`trabajo_private_registered_${dimension}_${slug}_${metric}`, label]))
  ]))
});
const publicInvestmentFunctions = {
  transport: 'Transporte', energy_mining: 'Energía y minería', water_sanitation: 'Agua y saneamiento',
  housing_urbanism: 'Vivienda y urbanismo', science_technology: 'Ciencia y técnica',
  education_culture: 'Educación y cultura', health: 'Salud', defense: 'Defensa'
};
const capitalExpenditureFunctions = {
  energy: 'Energía', transport: 'Transporte', education: 'Educación',
  housing: 'Vivienda', water: 'Agua', other: 'Otros y fondos fiduciarios'
};
const publicSpendingCoverages = {
  consolidated: 'Consolidado', national: 'Nacional', provincial: 'Provincial', municipal: 'Municipal'
};
const publicSpendingFinalities = {
  state_operation: 'I. FUNCIONAMIENTO DEL ESTADO',
  social_spending: 'II. GASTO PÚBLICO SOCIAL',
  economic_services: 'III. GASTO PÚBLICO EN SERVICIOS ECONÓMICOS',
  public_debt_services: 'IV. SERVICIOS DE LA DEUDA PÚBLICA'
};
const publicSpendingFunctions = {
  general_administration: 'I.1. Administración general', justice: 'I.2. Justicia', defense_security: 'I.3. Defensa y seguridad',
  education_culture_science_technology: 'II.1. Educación, cultura y ciencia y técnica', basic_education: 'II.1.1. Educación básica',
  higher_university_education: 'II.1.2. Educación superior y universitaria', science_technology: 'II.1.3. Ciencia y técnica',
  culture: 'II.1.4. Cultura', unspecified_education_culture: 'II.1.5. Educación y cultura sin discriminar', health: 'II.2. Salud',
  public_health_care: 'II.2.1. Atención pública de la salud', health_insurance_care: 'II.2.2. Obras sociales - Atención de la salud',
  inssjyp_health_care: 'II.2.3. INSSJyP - Atención de la salud', drinking_water_sewerage: 'II.3. Agua potable y alcantarillado',
  housing_urbanism: 'II.4. Vivienda y urbanismo', social_promotion_assistance: 'II.5. Promoción y asistencia social',
  public_social_promotion_assistance: 'II.5.1. Promoción y asistencia social pública',
  health_insurance_social_benefits: 'II.5.2. Obras sociales - Prestaciones sociales',
  inssjyp_social_benefits: 'II.5.3. INSSJyP - Prestaciones sociales', social_security: 'II.6. Previsión social', labor: 'II.7. Trabajo',
  employment_programs_unemployment_insurance: 'II.7.1. Programas de empleo y seguro de desempleo',
  family_allowances: 'II.7.2. Asignaciones familiares', other_urban_services: 'II.8. Otros servicios urbanos',
  primary_production: 'III.1. Producción primaria', energy_fuel: 'III.2. Energía y combustible', industry: 'III.3. Industria',
  services: 'III.4. Servicios', transport: 'III.4.1. Transporte', communications: 'III.4.2. Comunicaciones',
  other_economic_services: 'III.5. Otros gastos en servicios económicos', holdout_interest: 'IV.1  Pago intereses Holdouts (estimado)'
};
const publicSpendingMetrics = Object.fromEntries(Object.entries(publicSpendingCoverages).flatMap(([coverage, label]) => [
  [`${coverage}_gdp`, `${label} · % del PIB`], [`${coverage}_share`, `${label} · % del gasto total`]
]));
const publicSpendingUnits = Object.fromEntries(Object.keys(publicSpendingMetrics).map(key => [key, '%']));
const publicSpendingFinalitySeries = Object.fromEntries(Object.keys(publicSpendingMetrics).map(metric => [metric,
  Object.fromEntries(Object.entries(publicSpendingFinalities).map(([slug, label]) => [`mecon_public_spending_${metric}_${slug}`, label]))
]));

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
    id: 'actividad', eyebrow: 'ACTIVIDAD', title: 'Actividad económica', intro: 'EMAE mensual y desempeño sectorial. Serie general base 2004=100 e índices sectoriales con enero de 2020=100.', file: 'emae.csv',
    charts: [
      { title: 'EMAE', subtitle: 'Índice desestacionalizado y tendencia-ciclo', unit: 'índice', series: { indec_emae_sa_index: 'Desestacionalizado', indec_emae_trend_cycle_index: 'Tendencia-ciclo' }},
      { title: 'Actividad por sector', subtitle: 'Compará el nivel relativo o la variación interanual de cada sector', unit: 'índice', composite: {
        sectors, metrics: { index_jan_2020_100: 'Nivel (ene-20=100)', yoy: 'Variación interanual' }, units: { index_jan_2020_100: 'índice', yoy: '%' },
        seriesPattern: 'indec_emae_sector_{sector}_{metric}', dimensionLabel: 'Sector', defaultSector: 'manufacturing', defaultMetric: 'index_jan_2020_100'
      }}
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
    id: 'consumo-privado', eyebrow: 'CUENTAS NACIONALES', title: 'Consumo privado', intro: 'Gasto de consumo final privado agregado publicado trimestralmente por el INDEC.', file: 'gdp.csv',
    warning: 'Es un componente trimestral de la demanda del PIB y no un indicador mensual. El nivel real está expresado a precios constantes de 2004; la participación en el PIB se calcula con valores corrientes del mismo período.',
    charts: [
      { title: 'Consumo privado real', subtitle: 'Nivel y variaciones oficiales', unit: 'M ARS 2004', metricToggle: { default: 'sa_level', labels: { sa_level: 'Nivel desestacionalizado', qoq: 'Variación trimestral', yoy: 'Variación interanual', annual_level: 'Nivel anual', annual_growth: 'Variación anual' }, units: { sa_level: 'M ARS 2004', qoq: '%', yoy: '%', annual_level: 'M ARS 2004', annual_growth: '%' }, seriesByMetric: { sa_level: { indec_private_consumption_sa_constant_2004: 'Consumo privado' }, qoq: { indec_private_consumption_sa_qoq: 'Consumo privado' }, yoy: { indec_private_consumption_growth_quarterly: 'Consumo privado' }, annual_level: { indec_private_consumption_constant_2004_annual: 'Consumo privado' }, annual_growth: { indec_private_consumption_growth_annual: 'Consumo privado' } } }, series: { indec_private_consumption_sa_constant_2004: 'Consumo privado' } },
      { title: 'Consumo privado sobre PIB', subtitle: 'Participación a precios corrientes', unit: '% del PIB', metricToggle: { default: 'quarterly', labels: { quarterly: 'Trimestral', annual: 'Anual' }, units: { quarterly: '%', annual: '%' }, seriesByMetric: { quarterly: { indec_private_consumption_gdp_share_quarterly: 'Consumo privado' }, annual: { indec_private_consumption_gdp_share_annual: 'Consumo privado' } } }, series: { indec_private_consumption_gdp_share_quarterly: 'Consumo privado' } }
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
    id: 'empleo-sector', eyebrow: 'MERCADO LABORAL', title: 'Empleo registrado por sector', intro: 'Puestos de trabajo asalariados privados registrados, desestacionalizados y abiertos por rama de actividad.', file: 'registered_employment.csv',
    warning: 'La serie cubre empleo asalariado privado registrado en el SIPA: no representa todo el empleo ni incluye trabajo no registrado, empleo público o trabajo independiente. Los últimos datos son provisorios y pueden revisarse.',
    charts: [{ title: 'Puestos de trabajo por sector', subtitle: 'Nivel, índice comparable o variación contra igual mes del año anterior', unit: 'miles de personas', defaultVisibleByMetric: { level: ['trabajo_private_registered_sector_manufacturing_level', 'trabajo_private_registered_sector_construction_level', 'trabajo_private_registered_sector_commerce_level', 'trabajo_private_registered_sector_agriculture_level'], index: ['trabajo_private_registered_sector_manufacturing_index', 'trabajo_private_registered_sector_construction_index', 'trabajo_private_registered_sector_commerce_index', 'trabajo_private_registered_sector_agriculture_index'], yoy: ['trabajo_private_registered_sector_manufacturing_yoy', 'trabajo_private_registered_sector_construction_yoy', 'trabajo_private_registered_sector_commerce_yoy', 'trabajo_private_registered_sector_agriculture_yoy'] }, metricToggle: registeredEmploymentMetricToggle('sector', registeredEmploymentSectors), series: registeredEmploymentMetricToggle('sector', registeredEmploymentSectors).seriesByMetric.level }]
  },
  {
    id: 'empleo-provincia', eyebrow: 'MERCADO LABORAL', title: 'Empleo registrado por provincia', intro: 'Puestos de trabajo asalariados privados registrados, desestacionalizados y abiertos por jurisdicción.', file: 'registered_employment.csv',
    warning: 'La asignación geográfica corresponde a la localización declarada del puesto en el SIPA. La serie no incluye empleo privado no registrado, empleo público ni trabajo independiente; los últimos datos son provisorios.',
    charts: [{ title: 'Puestos de trabajo por provincia', subtitle: 'Nivel, índice comparable o variación contra igual mes del año anterior', unit: 'miles de personas', defaultVisibleByMetric: { level: ['trabajo_private_registered_province_buenos_aires_level', 'trabajo_private_registered_province_caba_level', 'trabajo_private_registered_province_cordoba_level', 'trabajo_private_registered_province_santa_fe_level'], index: ['trabajo_private_registered_province_buenos_aires_index', 'trabajo_private_registered_province_caba_index', 'trabajo_private_registered_province_cordoba_index', 'trabajo_private_registered_province_santa_fe_index'], yoy: ['trabajo_private_registered_province_buenos_aires_yoy', 'trabajo_private_registered_province_caba_yoy', 'trabajo_private_registered_province_cordoba_yoy', 'trabajo_private_registered_province_santa_fe_yoy'] }, metricToggle: registeredEmploymentMetricToggle('province', registeredEmploymentProvinces), series: registeredEmploymentMetricToggle('province', registeredEmploymentProvinces).seriesByMetric.level }]
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
    id: 'comercio', eyebrow: 'SECTOR EXTERNO', title: 'Comercio exterior', intro: 'Exportaciones, importaciones y saldo comercial de bienes.', file: 'trade.csv',
    charts: [
      { title: 'Intercambio comercial argentino', subtitle: 'Millones de dólares por mes', unit: 'USD M', series: { indec_trade_exports: 'Exportaciones', indec_trade_imports: 'Importaciones', indec_trade_balance: 'Saldo' }},
      { title: 'Saldo comercial', subtitle: 'Elegí el resultado mensual, el cierre anual o la diferencia contra igual mes del año anterior', unit: 'USD M', includeZero: true, metricToggle: { default: 'monthly', labels: { monthly: 'Saldo mensual', annual: 'Saldo anual', yoy_change: 'Variación interanual' }, seriesByMetric: { monthly: { indec_trade_balance: 'Saldo' }, annual: { indec_trade_balance_annual: 'Saldo anual' }, yoy_change: { indec_trade_balance_yoy_change: 'Diferencia interanual' } } }, series: { indec_trade_balance: 'Saldo' } }
    ]
  },
  {
    id: 'reservas', eyebrow: 'SECTOR EXTERNO', title: 'Reservas internacionales', intro: 'Stock diario de reservas internacionales brutas del Banco Central. Las cifras son provisorias y pueden cambiar por valuación.', file: 'reserves.csv',
    charts: [{ title: 'Reservas brutas del BCRA', subtitle: 'Millones de dólares; cifras oficiales provisorias', unit: 'USD M', defaultRange: '5Y', series: { bcra_gross_international_reserves: 'Reservas brutas' }}]
  },
  {
    id: 'reservas-netas', eyebrow: 'SECTOR EXTERNO', title: 'Reservas internacionales netas', intro: 'Reconstrucción diaria de los activos de reserva disponibles luego de descontar encajes, swap con China, obligaciones con organismos internacionales y repos a un año.', file: 'net_reserves.csv',
    warning: 'Serie calculada por DatArg, no publicada oficialmente por el BCRA. Combina datos diarios, semanales y mensuales; entre publicaciones se arrastra o estima el último componente disponible y luego se recalibra.',
    charts: [
      { title: 'Reservas netas', subtitle: 'Millones de dólares; definición corriente de mercado', unit: 'USD M', series: { bcra_net_international_reserves: 'Reservas netas' }},
      { title: 'Deducciones de las reservas brutas', subtitle: 'Componentes descontados, en millones de dólares', unit: 'USD M', series: { bcra_reserve_requirements_fx: 'Encajes', bcra_china_swap: 'Swap China', bcra_international_organizations_liability: 'OOII', bcra_repos_up_to_one_year: 'Repos ≤ 1 año' }}
    ]
  },
  {
    id: 'depositos-dolares', eyebrow: 'SISTEMA FINANCIERO', title: 'Depósitos privados en dólares', intro: 'Saldo de los depósitos en moneda extranjera del sector privado no financiero en el sistema bancario.', file: 'private_fx_deposits.csv',
    charts: [{ title: 'Depósitos privados en dólares', subtitle: 'Saldo al cierre de cada mes; millones de dólares', unit: 'USD M', defaultRange: '10Y', series: { bcra_private_nonfinancial_fx_deposits: 'Depósitos privados' }}]
  },
  {
    id: 'dolar', eyebrow: 'MERCADO CAMBIARIO', title: 'Tipos de cambio', intro: 'Cotizaciones históricas de venta del dólar oficial, blue, MEP y contado con liquidación.', file: 'exchange_rates.csv',
    charts: [{ title: 'Dólar por mercado', subtitle: 'Pesos argentinos por dólar', unit: 'ARS/USD', defaultRange: '5Y', series: { argentinadatos_usd_official_retail_sell: 'Oficial', argentinadatos_usd_blue_sell: 'Blue', argentinadatos_usd_mep_sell: 'MEP', argentinadatos_usd_ccl_sell: 'CCL' }}]
  },
  {
    id: 'itcrm', eyebrow: 'COMPETITIVIDAD CAMBIARIA', title: 'Tipo de cambio real', intro: 'ITCRM e índices bilaterales reales publicados diariamente por el Banco Central. Valores superiores a 100 indican una depreciación real respecto de la base.', file: 'real_exchange_rate.csv',
    warning: 'Base 17 de diciembre de 2015=100. Los datos son provisorios y están sujetos a revisión; el ITCRM pondera los tipos de cambio reales bilaterales según el comercio exterior argentino.',
    charts: [{ title: 'ITCRM y bilaterales', subtitle: 'Índices diarios; seleccioná uno o más socios comerciales', unit: 'índice', defaultRange: '5Y', defaultVisible: ['bcra_itcrm'], series: { bcra_itcrm: 'ITCRM', bcra_itcrb_brazil: 'Brasil', bcra_itcrb_united_states: 'Estados Unidos', bcra_itcrb_china: 'China', bcra_itcrb_euro_area: 'Zona Euro' }}]
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
    id: 'intervencion', eyebrow: 'MERCADO CAMBIARIO', title: 'Intervención cambiaria', intro: 'Compras y ventas spot del BCRA y una medición mensual ajustada por el cambio de su posición en futuros de dólar.', file: 'fx_intervention.csv',
    warning: 'La intervención ajustada es un cálculo de DatArg, no una serie oficial: compras spot menos el aumento mensual de la posición neta vendida en futuros. Un resultado positivo representa una fuerza neta compradora y uno negativo, una fuerza neta vendedora o de contención del dólar, todo lo demás constante. El BCRA solo publica su posición propia en futuros al cierre de cada mes: el interés abierto diario del mercado no permite identificar al Banco Central. Los futuros se liquidan en pesos y no son un flujo de reservas. La medición todavía excluye operaciones directas con el Tesoro, bonos dólar linked y otras intervenciones del sector público.',
    charts: [{ title: 'Compras y ventas de divisas del BCRA', subtitle: 'Flujo neto en millones de dólares', unit: 'USD M', type: 'bar', includeZero: true, defaultRange: '5Y', metricToggle: {
      default: 'daily',
      labels: { daily: 'Diario', monthly: 'Acumulado mensual', annual: 'Acumulado anual' },
      seriesByMetric: {
        daily: { bcra_fx_intervention_daily: 'Intervención neta diaria' },
        monthly: { bcra_fx_intervention_monthly: 'Acumulado mensual' },
        annual: { bcra_fx_intervention_annual: 'Acumulado anual' }
      }
    }, series: { bcra_fx_intervention_daily: 'Intervención neta diaria' } },
    { title: 'Intervención neta ajustada por futuros', subtitle: 'Flujo mensual y posición abierta del BCRA; millones de dólares', unit: 'USD M', type: 'bar', includeZero: true, defaultRange: '5Y', defaultVisibleByMetric: { adjusted: ['bcra_fx_intervention_adjusted_monthly'], futures: ['bcra_fx_futures_net_short_change'], position: ['bcra_fx_futures_net_short_position'] }, metricToggle: {
      default: 'adjusted',
      labels: { adjusted: 'Intervención ajustada', futures: 'Intervención en futuros', position: 'Posición abierta' },
      seriesByMetric: {
        adjusted: { bcra_fx_intervention_monthly: 'Compras spot', bcra_fx_futures_net_short_change: 'Cambio posición vendida', bcra_fx_intervention_adjusted_monthly: 'Intervención ajustada' },
        futures: { bcra_fx_futures_net_short_change: 'Cambio posición vendida' },
        position: { bcra_fx_futures_net_short_position: 'Posición neta vendida', bcra_fx_futures_short_position: 'Posición vendida bruta', bcra_fx_futures_long_position: 'Posición comprada' }
      }
    }, series: { bcra_fx_intervention_monthly: 'Compras spot', bcra_fx_futures_net_short_change: 'Cambio posición vendida', bcra_fx_intervention_adjusted_monthly: 'Intervención ajustada' } }]
  },
  {
    id: 'liquidez-tesoro', eyebrow: 'TESORO NACIONAL', title: 'Liquidez del Tesoro en el BCRA', intro: 'Saldos de las cuentas del Gobierno Nacional en pesos y en moneda extranjera depositadas en el Banco Central.', file: 'treasury_liquidity.csv',
    warning: 'Son saldos contables, no flujos de intervención. La cuenta en dólares es un cálculo de DatArg: el saldo oficial en moneda extranjera, que el BCRA publica convertido a pesos, se divide por su tipo de cambio de valuación. Las variaciones miden cambios entre saldos informados y pueden responder a cobros, pagos de deuda, operaciones con organismos u otros movimientos del Tesoro; por sí solas no prueban una intervención cambiaria. Se omiten las fechas futuras o provisionales publicadas con saldo cero.',
    charts: [
      { title: 'Cuenta del Tesoro en pesos', subtitle: 'Saldo y variación diaria o mensual', unit: 'M ARS', defaultRange: '5Y', metricToggle: { default: 'daily_stock', labels: { daily_stock: 'Saldo diario', daily_change: 'Variación diaria', monthly_stock: 'Saldo mensual', monthly_change: 'Variación mensual' }, units: { daily_stock: 'M ARS', daily_change: 'M ARS', monthly_stock: 'M ARS', monthly_change: 'M ARS' }, types: { daily_stock: 'line', daily_change: 'bar', monthly_stock: 'line', monthly_change: 'bar' }, seriesByMetric: { daily_stock: { bcra_treasury_deposits_ars_daily: 'Saldo en pesos' }, daily_change: { bcra_treasury_deposits_ars_daily_change: 'Variación diaria del saldo' }, monthly_stock: { bcra_treasury_deposits_ars: 'Saldo en pesos' }, monthly_change: { bcra_treasury_deposits_ars_monthly_change: 'Variación mensual del saldo' } } }, series: { bcra_treasury_deposits_ars_daily: 'Saldo en pesos' } },
      { title: 'Cuenta del Tesoro en dólares', subtitle: 'Saldo estimado y variación diaria o mensual', unit: 'USD M', defaultRange: '5Y', metricToggle: { default: 'daily_stock', labels: { daily_stock: 'Saldo diario', daily_change: 'Variación diaria', monthly_stock: 'Saldo mensual', monthly_change: 'Variación mensual' }, units: { daily_stock: 'USD M', daily_change: 'USD M', monthly_stock: 'USD M', monthly_change: 'USD M' }, types: { daily_stock: 'line', daily_change: 'bar', monthly_stock: 'line', monthly_change: 'bar' }, seriesByMetric: { daily_stock: { bcra_treasury_deposits_usd_daily: 'Saldo estimado en dólares' }, daily_change: { bcra_treasury_deposits_usd_daily_change: 'Variación diaria del saldo' }, monthly_stock: { bcra_treasury_deposits_usd: 'Saldo estimado en dólares' }, monthly_change: { bcra_treasury_deposits_usd_monthly_change: 'Variación mensual del saldo' } } }, series: { bcra_treasury_deposits_usd_daily: 'Saldo estimado en dólares' } }
    ]
  },
  {
    id: 'dividendos', eyebrow: 'MERCADO CAMBIARIO', title: 'Giros de utilidades y dividendos', intro: 'Pagos de utilidades y dividendos al exterior efectivamente cursados por el mercado de cambios.', file: 'profit_dividends.csv',
    warning: 'Los valores muestran egresos cambiarios, no utilidades contables devengadas ni reinvertidas. La vista anual incluye únicamente años calendario completos; las regulaciones cambiarias pueden afectar la comparación entre períodos.',
    charts: [{ title: 'Giros de utilidades y dividendos al exterior', subtitle: 'Flujos en millones de dólares', unit: 'USD M', type: 'bar', includeZero: true, defaultRange: '5Y', metricToggle: {
      default: 'monthly',
      labels: { monthly: 'Mensual', annual: 'Anual' },
      seriesByMetric: {
        monthly: { bcra_profit_dividend_outflows_monthly: 'Giros mensuales' },
        annual: { bcra_profit_dividend_outflows_annual: 'Giros anuales' }
      }
    }, series: { bcra_profit_dividend_outflows_monthly: 'Giros mensuales' } }]
  },
  {
    id: 'agregados-monetarios', eyebrow: 'MONEDA Y CRÉDITO', title: 'Dinero y agregados monetarios', intro: 'Base monetaria diaria, sus componentes y medidas progresivamente más amplias de dinero publicadas por el BCRA.', file: 'monetary_aggregates.csv',
    warning: 'Los saldos mensuales son de fin de mes. M1, M2, M3 de residentes y M3 total amplían sucesivamente el conjunto de activos monetarios; por eso no deben sumarse entre sí. M3 total es la medida histórica más amplia y consistente del archivo oficial. No se la etiqueta como M4 ni se la empalma con la “Base Monetaria Amplia” usada como referencia operativa del régimen monetario desde 2024, porque son conceptos diferentes y no existe una serie histórica homogénea publicada con esa definición.',
    charts: [
      { title: 'Base monetaria y componentes', subtitle: 'Saldos diarios en millones de pesos', unit: 'M ARS', defaultVisible: ['bcra_monetary_base_daily'], series: { bcra_monetary_base_daily: 'Base monetaria', bcra_currency_circulation_daily: 'Circulación monetaria', bcra_currency_public_daily: 'Billetes y monedas en poder del público', bcra_cash_financial_institutions_daily: 'Efectivo en entidades financieras', bcra_bank_current_accounts_daily: 'Cuentas corrientes de entidades en el BCRA' } },
      { title: 'Agregados monetarios', subtitle: 'Compará poder de compra, profundidad monetaria o saldos nominales', unit: 'índice', defaultVisibleByMetric: { real: ['bcra_monetary_base_monthly_real_index', 'bcra_m2_total_monthly_real_index', 'bcra_m3_total_monthly_real_index'], gdp: ['bcra_monetary_base_monthly_gdp_ratio', 'bcra_m2_total_monthly_gdp_ratio', 'bcra_m3_total_monthly_gdp_ratio'], nominal: ['bcra_monetary_base_monthly', 'bcra_m2_total_monthly', 'bcra_m3_total_monthly'] }, metricToggle: { default: 'real', labels: { real: 'Nivel real (dic-23=100)', gdp: 'Porcentaje del PIB', nominal: 'Saldo nominal' }, units: { real: 'índice', gdp: '%', nominal: 'M ARS' }, seriesByMetric: { real: { bcra_monetary_base_monthly_real_index: 'Base monetaria', bcra_m1_total_monthly_real_index: 'M1', bcra_m2_total_monthly_real_index: 'M2', bcra_m3_resident_monthly_real_index: 'M3 residentes', bcra_m3_total_monthly_real_index: 'M3 total' }, gdp: { bcra_monetary_base_monthly_gdp_ratio: 'Base monetaria', bcra_m1_total_monthly_gdp_ratio: 'M1', bcra_m2_total_monthly_gdp_ratio: 'M2', bcra_m3_resident_monthly_gdp_ratio: 'M3 residentes', bcra_m3_total_monthly_gdp_ratio: 'M3 total' }, nominal: { bcra_monetary_base_monthly: 'Base monetaria', bcra_m1_total_monthly: 'M1', bcra_m2_total_monthly: 'M2', bcra_m3_resident_monthly: 'M3 residentes', bcra_m3_total_monthly: 'M3 total' } } }, series: { bcra_monetary_base_monthly_real_index: 'Base monetaria', bcra_m2_total_monthly_real_index: 'M2', bcra_m3_total_monthly_real_index: 'M3 total' } }
    ]
  },
  {
    id: 'tasas', eyebrow: 'SISTEMA FINANCIERO', title: 'Tasas de interés', intro: 'Tasas bancarias, exigencias de liquidez del BCRA y estructura temporal de rendimientos de la deuda en pesos.', file: 'interest_rates.csv',
    warning: 'La tasa de encajes es la exigencia normativa promedio ponderada sobre depósitos y otras obligaciones. No es una alícuota única para todos los depósitos ni el ratio contable de liquidez de cada banco: cambia con la composición por moneda, plazo e instrumento. Desde agosto de 2025 el BCRA restableció el cumplimiento diario de los requisitos de efectivo mínimo.',
    charts: [
      { title: 'Tasas mayoristas', subtitle: 'Tasa nominal anual', unit: '% TNA', defaultRange: '5Y', series: { bcra_badlar_private_tna: 'BADLAR', bcra_tamar_private_tna: 'TAMAR' }},
      { title: 'Encajes bancarios', subtitle: 'Exigencia normativa promedio ponderada sobre depósitos y otras obligaciones', file: 'reserve_requirements.csv', unit: '%', defaultRange: '10Y', defaultVisible: ['bcra_reserve_requirement_total'], series: { bcra_reserve_requirement_total: 'Total', bcra_reserve_requirement_ars: 'Pesos', bcra_reserve_requirement_fx: 'Moneda extranjera' }},
      { title: 'Curvas de deuda en pesos', subtitle: 'TIR efectiva anual por plazo al vencimiento', file: 'yield_curves.csv', renderer: 'yield-curves' }
    ]
  },
  {
    id: 'credito', eyebrow: 'SISTEMA FINANCIERO', title: 'Crédito privado y sector público', intro: 'Préstamos de las entidades financieras al sector privado no financiero y exposición de los bancos al sector público.', file: 'credit.csv',
    warning: 'El índice real deflacta los saldos con el IPC nacional y fija diciembre de 2019 = 100. La vista sobre PIB divide los promedios mensuales de préstamos por el PIB nominal anualizado disponible; los puntos recientes publicados por el BCRA reemplazan el cálculo de DatArg. Los préstamos en moneda extranjera se convierten a pesos al tipo de cambio de cada período. La exposición pública ampliada excluye Letras y Notas del BCRA.',
    charts: [
      { title: 'Crédito al sector privado no financiero', subtitle: 'Evolución real y profundidad respecto de la economía', explanation: 'La apertura por moneda usa los promedios mensuales del Informe Monetario Diario. El crédito en dólares se convierte a pesos antes de dividir por el PIB, por eso los componentes pueden sumarse para obtener el total. Los últimos puntos publicados por el BCRA se usan como control y prevalecen sobre la estimación de DatArg.', unit: 'índice', defaultVisibleByMetric: { real_index: ['bcra_private_nonfinancial_credit_real_index'], gdp_ratio: ['bcra_private_nonfinancial_credit_gdp_ratio'] }, metricToggle: { default: 'real_index', labels: { real_index: 'Nivel real (dic-19=100)', gdp_ratio: 'Porcentaje del PIB' }, units: { real_index: 'índice', gdp_ratio: '%' }, seriesByMetric: { real_index: { bcra_private_nonfinancial_credit_real_index: 'Total' }, gdp_ratio: { bcra_private_nonfinancial_credit_ars_gdp_ratio: 'En pesos', bcra_private_nonfinancial_credit_fx_ars_gdp_ratio: 'En moneda extranjera', bcra_private_nonfinancial_credit_gdp_ratio: 'Total' } } }, series: { bcra_private_nonfinancial_credit_real_index: 'Total' } },
      { title: 'Préstamos al sector público', subtitle: 'Gobiernos y empresas u otros entes públicos', unit: 'índice', metricToggle: { default: 'real_index', labels: { real_index: 'Nivel real (dic-19=100)', gdp_ratio: 'Porcentaje del PIB' }, units: { real_index: 'índice', gdp_ratio: '%' }, seriesByMetric: { real_index: { bcra_public_loans_total_real_index: 'Total sector público', bcra_public_loans_government_real_index: 'Gobiernos', bcra_public_loans_enterprises_real_index: 'Empresas y otros entes' }, gdp_ratio: { bcra_public_loans_total_gdp_ratio: 'Total sector público', bcra_public_loans_government_gdp_ratio: 'Gobiernos', bcra_public_loans_enterprises_gdp_ratio: 'Empresas y otros entes' } } }, series: { bcra_public_loans_total_real_index: 'Total sector público', bcra_public_loans_government_real_index: 'Gobiernos', bcra_public_loans_enterprises_real_index: 'Empresas y otros entes' } },
      { title: 'Exposición ampliada al sector público', subtitle: 'Préstamos más títulos públicos en poder de las entidades financieras', unit: 'índice', defaultVisibleByMetric: { real_index: ['bcra_public_exposure_total_real_index'], gdp_ratio: ['bcra_public_exposure_total_gdp_ratio'] }, metricToggle: { default: 'real_index', labels: { real_index: 'Nivel real (dic-19=100)', gdp_ratio: 'Porcentaje del PIB' }, units: { real_index: 'índice', gdp_ratio: '%' }, seriesByMetric: { real_index: { bcra_public_exposure_total_real_index: 'Exposición total', bcra_public_loans_total_real_index: 'Préstamos', bcra_public_exposure_securities_real_index: 'Títulos públicos' }, gdp_ratio: { bcra_public_exposure_total_gdp_ratio: 'Exposición total', bcra_public_loans_total_gdp_ratio: 'Préstamos', bcra_public_exposure_securities_gdp_ratio: 'Títulos públicos' } } }, series: { bcra_public_exposure_total_real_index: 'Exposición total', bcra_public_loans_total_real_index: 'Préstamos', bcra_public_exposure_securities_real_index: 'Títulos públicos' } }
    ]
  },
  {
    id: 'fiscal', eyebrow: 'FINANZAS PÚBLICAS', title: 'Recaudación y resultado fiscal', intro: 'Ingresos tributarios y resultados mensuales del Sector Público Nacional no Financiero medidos por base caja.', file: 'fiscal.csv',
    warning: 'El resultado primario se calcula antes de intereses. El resultado financiero —o fiscal total— los incluye. Los niveles reales están expresados a precios de diciembre de 2025 mediante el IPC nacional; las vistas anuales y en porcentaje del PIB incluyen solo años calendario completos.',
    charts: [
      { title: 'Recaudación tributaria', subtitle: 'Elegí entre crecimiento real, nivel real y valores nominales', unit: '%', metricToggle: { default: 'real_yoy', labels: { real_yoy: 'Variación real interanual', real_monthly: 'Nivel real mensual', annual_yoy: 'Variación real anual', real_annual: 'Nivel real anual', nominal: 'Nivel nominal mensual' }, units: { real_yoy: '%', real_monthly: 'M ARS dic-25', annual_yoy: '%', real_annual: 'M ARS dic-25', nominal: 'M ARS' }, seriesByMetric: { real_yoy: { mecon_tax_revenue_total_real_yoy: 'Recaudación total' }, real_monthly: { mecon_tax_revenue_total_real_monthly: 'Recaudación total' }, annual_yoy: { mecon_tax_revenue_total_real_annual_yoy: 'Recaudación total' }, real_annual: { mecon_tax_revenue_total_real_annual: 'Recaudación total' }, nominal: { mecon_tax_revenue_total_nominal_monthly: 'Recaudación total' } } }, series: { mecon_tax_revenue_total_real_yoy: 'Recaudación total' } },
      { title: 'Resultado fiscal', subtitle: 'Resultado primario y financiero del SPN', unit: 'M ARS dic-25', includeZero: true, metricToggle: { default: 'real_monthly', labels: { real_monthly: 'Mensual real', nominal: 'Mensual nominal', real_annual: 'Anual real', gdp: 'Anual como % del PIB' }, units: { real_monthly: 'M ARS dic-25', nominal: 'M ARS', real_annual: 'M ARS dic-25', gdp: '%' }, seriesByMetric: { real_monthly: { mecon_fiscal_primary_real_monthly: 'Resultado primario', mecon_fiscal_financial_real_monthly: 'Resultado financiero' }, nominal: { mecon_fiscal_primary_nominal_monthly: 'Resultado primario', mecon_fiscal_financial_nominal_monthly: 'Resultado financiero' }, real_annual: { mecon_fiscal_primary_real_annual: 'Resultado primario', mecon_fiscal_financial_real_annual: 'Resultado financiero' }, gdp: { mecon_fiscal_primary_annual_gdp: 'Resultado primario', mecon_fiscal_financial_annual_gdp: 'Resultado financiero' } } }, series: { mecon_fiscal_primary_real_monthly: 'Resultado primario', mecon_fiscal_financial_real_monthly: 'Resultado financiero' } }
    ]
  },
  {
    id: 'gasto-publico', eyebrow: 'FINANZAS PÚBLICAS', title: 'Gasto público consolidado', intro: 'Evolución anual del gasto público del Sector Público No Financiero, con apertura por nivel de gobierno, finalidad y función.', file: 'public_spending.csv',
    warning: 'La serie oficial está medida por devengado y consolida Nación, provincias y municipios para evitar duplicar transferencias entre niveles de gobierno. La participación en el gasto total es un cálculo de DatArg a partir de los porcentajes del PIB publicados. El último año disponible es provisorio.',
    charts: [
      { title: 'GASTO PÚBLICO TOTAL', subtitle: 'Comparación por nivel de gobierno; porcentaje del PIB', unit: '%', metricToggle: { default: 'consolidated', labels: publicSpendingCoverages, units: Object.fromEntries(Object.keys(publicSpendingCoverages).map(key => [key, '%'])), seriesByMetric: Object.fromEntries(Object.entries(publicSpendingCoverages).map(([coverage, label]) => [coverage, { [`mecon_public_spending_${coverage}_gdp_total`]: label }])) }, series: { mecon_public_spending_consolidated_gdp_total: 'Consolidado' } },
      { title: 'Composición por finalidad', subtitle: 'Clasificación funcional oficial en porcentaje del PIB o del gasto total', unit: '%', metricToggle: { default: 'consolidated_gdp', labels: publicSpendingMetrics, units: publicSpendingUnits, seriesByMetric: publicSpendingFinalitySeries }, series: publicSpendingFinalitySeries.consolidated_gdp },
      { title: 'Apertura por función', subtitle: 'Elegí una función oficial, la cobertura y la medida', unit: '%', composite: { sectors: publicSpendingFunctions, metrics: publicSpendingMetrics, units: publicSpendingUnits, seriesPattern: 'mecon_public_spending_{metric}_{sector}', dimensionLabel: 'Función', defaultSector: 'education_culture_science_technology', defaultMetric: 'consolidated_gdp' } }
    ]
  },
  {
    id: 'inversion-publica', eyebrow: 'FINANZAS PÚBLICAS', title: 'Inversión pública', intro: 'Evolución anual de la inversión pública nacional y su composición funcional.', file: 'public_investment.csv',
    warning: 'La inversión pública corresponde a la Administración Pública Nacional y se mide por devengado. Los gastos de capital corresponden al Sector Público Nacional y se miden por base caja, por lo que ambas series no son idénticas. Se excluyen las proyecciones y créditos vigentes de 2026 para mostrar únicamente años ejecutados.',
    charts: [
      { title: 'Inversión pública nacional', subtitle: 'Nivel real con 2019=100 o porcentaje del PIB', unit: 'índice', metricToggle: { default: 'real_index', labels: { real_index: 'Nivel real (2019=100)', gdp_ratio: 'Porcentaje del PIB' }, units: { real_index: 'índice', gdp_ratio: '%' }, seriesByMetric: { real_index: { jgm_public_investment_real_index: 'Inversión pública' }, gdp_ratio: { jgm_public_investment_gdp_ratio: 'Inversión pública' } } }, series: { jgm_public_investment_real_index: 'Inversión pública' } },
      { title: 'Componentes de la inversión pública', subtitle: 'Elegí una función y compará su nivel real o peso en el PIB', unit: 'índice', composite: { sectors: publicInvestmentFunctions, metrics: { real_index: 'Nivel real (2019=100)', gdp_ratio: 'Porcentaje del PIB' }, units: { real_index: 'índice', gdp_ratio: '%' }, seriesPattern: 'jgm_public_investment_function_{metric}_{sector}', dimensionLabel: 'Función', defaultSector: 'transport', defaultMetric: 'real_index' } },
      { title: 'Gastos de capital del SPN', subtitle: 'Ejecución base caja; nivel real con 2019=100 o porcentaje del PIB', unit: 'índice', metricToggle: { default: 'real_index', labels: { real_index: 'Nivel real (2019=100)', gdp_ratio: 'Porcentaje del PIB' }, units: { real_index: 'índice', gdp_ratio: '%' }, seriesByMetric: { real_index: { jgm_capital_expenditure_real_index: 'Gastos de capital' }, gdp_ratio: { jgm_capital_expenditure_gdp_ratio: 'Gastos de capital' } } }, series: { jgm_capital_expenditure_real_index: 'Gastos de capital' } },
      { title: 'Componentes del gasto de capital', subtitle: 'Apertura funcional disponible desde 2016', unit: 'índice', composite: { sectors: capitalExpenditureFunctions, metrics: { real_index: 'Nivel real (2019=100)', gdp_ratio: 'Porcentaje del PIB' }, units: { real_index: 'índice', gdp_ratio: '%' }, seriesPattern: 'jgm_capital_expenditure_function_{metric}_{sector}', dimensionLabel: 'Función', defaultSector: 'energy', defaultMetric: 'real_index' } }
    ]
  },
  {
    id: 'prevision-social', eyebrow: 'SEGURIDAD SOCIAL', title: 'Sistema previsional', intro: 'Gasto previsional, cobertura de las prestaciones contributivas con aportes corrientes y fuentes de financiamiento de ANSES.', file: 'pensions.csv',
    warning: 'La cobertura sigue la metodología homogénea de la Oficina de Presupuesto del Congreso: aportes y contribuciones a la seguridad social divididos por prestaciones contributivas y semicontributivas, incluidas las moratorias. Excluye PUAM, pensiones no contributivas y otras prestaciones no contributivas. La participación de los aportes en los recursos de ANSES es otro indicador: mide la composición de sus ingresos y, siguiendo al Anuario Estadístico, excluye Rentas de la Propiedad. No debe interpretarse como el porcentaje del gasto jubilatorio cubierto.',
    charts: [
      { file: 'public_spending.csv', title: 'Gasto previsional', subtitle: 'Previsión social consolidada; porcentaje del PIB', explanation: 'Mide el peso del gasto previsional en la economía. No indica qué proporción se financia con aportes.', unit: '%', series: { mecon_public_spending_consolidated_gdp_social_security: 'Gasto previsional' } },
      { title: 'Cobertura con aportes actuales', subtitle: 'Prestaciones contributivas y semicontributivas cubiertas por aportes y contribuciones', explanation: 'Compara aportes corrientes con jubilaciones contributivas y por moratoria. Incluye moratorias; excluye PUAM y otras prestaciones no contributivas.', unit: '%', series: { opc_contributory_semicontributory_coverage: 'Cobertura previsional' } },
      { title: 'Aportes dentro de los recursos de ANSES', subtitle: 'Participación anual; excluye Rentas de la Propiedad', explanation: 'Muestra qué parte de los ingresos de ANSES proviene de aportes y contribuciones. No mide cuánto gasto jubilatorio cubren.', unit: '%', series: { anses_contributions_resource_share: 'Aportes y contribuciones' } },
      { title: 'Recursos de ANSES', subtitle: 'Evolución anual de aportes e impuestos como porcentaje del PIB', explanation: 'Compara el tamaño de las dos fuentes principales de recursos respecto del PIB. Su perímetro contable difiere del indicador de cobertura.', unit: '%', series: { anses_contributions_gdp: 'Aportes y contribuciones', anses_tax_resources_gdp: 'Recursos tributarios' } },
      { title: 'Cómo se financia ANSES', subtitle: 'Composición de los recursos totales en 2023', explanation: 'Es una foto del origen de todos los ingresos de ANSES en 2023; no asigna cada fuente a una prestación específica.', unit: '%', series: { anses_financing_contributions_share: 'Aportes y contribuciones', anses_financing_taxes_share: 'Impuestos', anses_financing_treasury_share: 'Tesoro y contribuciones figurativas', anses_financing_other_share: 'Otros' } }
    ]
  },
  {
    id: 'fgs', eyebrow: 'SEGURIDAD SOCIAL', title: 'Fondo de Garantía de Sustentabilidad', intro: 'Patrimonio y composición de la cartera del FGS valuados al dólar contado con liquidación de cada cierre anual.', file: 'fgs.csv',
    warning: 'Cálculo de DatArg sobre los cierres nominales publicados por ANSES. Cada observación se convierte al CCL vendedor del último día disponible del año. La serie comienza en 2013 porque no se empalma el CCL con otros tipos de cambio. Las categorías se normalizan para mantener comparabilidad pese a cambios de clasificación entre informes.',
    charts: [
      { title: 'Patrimonio del FGS en CCL', subtitle: 'Cierres anuales; millones de USD al contado con liquidación', explanation: 'Valúa el patrimonio anual del fondo al dólar CCL de cada cierre. No representa recursos corrientes de ANSES ni cobertura anual de jubilaciones.', unit: 'USD M', series: { datarg_fgs_total_ccl_usd: 'Patrimonio total' } },
      { title: 'Composición del FGS', subtitle: 'Apertura comparable por grandes clases de activos', explanation: 'Muestra en qué activos está invertido el patrimonio del fondo. Puede verse como monto en USD CCL o como participación dentro de la cartera.', unit: 'USD M', defaultVisibleByMetric: { usd: ['datarg_fgs_public_securities_ccl_usd', 'datarg_fgs_shares_ccl_usd', 'datarg_fgs_infrastructure_ccl_usd'], share: ['datarg_fgs_public_securities_share', 'datarg_fgs_shares_share', 'datarg_fgs_infrastructure_share'] }, metricToggle: { default: 'usd', labels: { usd: 'Millones de USD CCL', share: 'Porcentaje de la cartera' }, units: { usd: 'USD M', share: '%' }, seriesByMetric: { usd: { datarg_fgs_public_securities_ccl_usd: 'Títulos públicos nacionales', datarg_fgs_other_public_assets_ccl_usd: 'Otros activos públicos', datarg_fgs_shares_ccl_usd: 'Acciones', datarg_fgs_infrastructure_ccl_usd: 'Proyectos e infraestructura', datarg_fgs_loans_ccl_usd: 'Préstamos', datarg_fgs_private_fixed_income_liquidity_ccl_usd: 'Renta fija privada y liquidez', datarg_fgs_cash_other_ccl_usd: 'Disponibilidades y otros' }, share: { datarg_fgs_public_securities_share: 'Títulos públicos nacionales', datarg_fgs_other_public_assets_share: 'Otros activos públicos', datarg_fgs_shares_share: 'Acciones', datarg_fgs_infrastructure_share: 'Proyectos e infraestructura', datarg_fgs_loans_share: 'Préstamos', datarg_fgs_private_fixed_income_liquidity_share: 'Renta fija privada y liquidez', datarg_fgs_cash_other_share: 'Disponibilidades y otros' } } }, series: { datarg_fgs_public_securities_ccl_usd: 'Títulos públicos nacionales', datarg_fgs_shares_ccl_usd: 'Acciones', datarg_fgs_infrastructure_ccl_usd: 'Proyectos e infraestructura' } }
    ]
  },
  {
    id: 'deuda', eyebrow: 'FINANZAS PÚBLICAS', title: 'Deuda pública', intro: 'Deuda bruta de la Administración Central y tres perímetros complementarios de pasivos del BCRA.', file: 'public_debt.csv', warning: 'Las series del Tesoro y del BCRA no se suman ni equivalen a deuda neta consolidada. “Remunerados” conserva la selección de letras, LELIQ/NOTALIQ y pases. “Amplios” suma, sin duplicar subtotales, pasivos monetarios, títulos del BCRA, pases pasivos, depósitos del Gobierno y asignaciones de DEG informados en la planilla diaria. “Total contable” es el renglón TOTAL DEL PASIVO del balance semanal resumido y por eso también incluye otras obligaciones contables. Los importes en pesos se convierten a USD con el tipo de cambio de valuación de cada fuente.',
    charts: [
      { title: 'Deuda bruta del Tesoro', subtitle: 'Administración Central; nivel en USD o proporción del PIB', unit: 'USD M', metricToggle: { default: 'usd', labels: { usd: 'Millones de USD', gdp: 'Porcentaje del PIB' }, units: { usd: 'USD M', gdp: '%' }, seriesByMetric: { usd: { mecon_gross_central_government_debt: 'Tesoro' }, gdp: { mecon_gross_central_government_debt_gdp_ratio: 'Tesoro' } } }, series: { mecon_gross_central_government_debt: 'Tesoro' }},
      { title: 'Pasivos del BCRA', subtitle: 'Elegí el perímetro: remunerados, agregado amplio o total contable', unit: 'USD M', metricToggle: { default: 'remunerated', labels: { remunerated: 'Remunerados', broad: 'Amplios', accounting: 'Total contable' }, units: { remunerated: 'USD M', broad: 'USD M', accounting: 'USD M' }, seriesByMetric: { remunerated: { bcra_interest_bearing_liabilities: 'Pasivos remunerados' }, broad: { bcra_broad_financial_liabilities: 'Pasivos amplios' }, accounting: { bcra_total_accounting_liabilities: 'Pasivo contable total' } } }, series: { bcra_interest_bearing_liabilities: 'Pasivos remunerados' }}
    ]
  },
  {
    id: 'vencimientos', eyebrow: 'FINANZAS PÚBLICAS', title: 'Vencimientos del Tesoro',
    intro: 'Cronograma mensual de capital e intereses de la deuda bruta de la Administración Central, con apertura por grupo e instrumento.',
    file: 'treasury_maturities.csv', renderer: 'maturities',
    warning: 'Es un cronograma proyectado, no pagos efectivamente realizados. Cada edición conserva la fecha de corte del informe y valúa los compromisos con el stock de deuda y los tipos de cambio vigentes en esa fecha.',
    charts: [{ title: 'Perfil mensual de vencimientos', subtitle: 'Capital e intereses; millones de USD' }]
  },
  {
    id: 'deuda-neta', eyebrow: 'FINANZAS PÚBLICAS', title: 'Deuda estatal neta', intro: 'Medición comparable que excluye deuda intrasector público e incorpora los pasivos financieros del BCRA y las reservas netas.', file: 'consolidated_debt.csv',
    warning: 'Estimación, no estadística oficial. Los cortes antiguos siguen la fórmula comparable de Chequeado/Aurum. Desde 2023 se muestra por separado la medición anual de Facimex, que consolida Tesoro y BCRA, elimina tenencias intraestatales y resta reservas netas y depósitos del Tesoro. El nivel 2024 se deriva del ratio Facimex y el PIB corriente del Banco Mundial; no se interpolan períodos.',
    charts: [
      { title: 'Deuda estatal neta consolidada', subtitle: 'Cortes históricos y secuencia anual desde 2023', unit: 'USD M', metricToggle: { default: 'usd', labels: { usd: 'Millones de USD', gdp: 'Porcentaje del PIB' }, units: { usd: 'USD M', gdp: '%' }, seriesByMetric: { usd: { estimated_comparable_net_public_debt: 'Cortes Chequeado/Aurum', estimated_facimex_net_consolidated_debt: 'Facimex desde 2023' }, gdp: { estimated_comparable_net_public_debt_gdp: 'Cortes Chequeado/Aurum', estimated_facimex_net_consolidated_debt_gdp: 'Facimex desde 2023' } } }, series: { estimated_facimex_net_consolidated_debt: 'Facimex desde 2023' }}
    ]
  }
];
