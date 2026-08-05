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
const publicInvestmentFunctions = {
  transport: 'Transporte', energy_mining: 'Energía y minería', water_sanitation: 'Agua y saneamiento',
  housing_urbanism: 'Vivienda y urbanismo', science_technology: 'Ciencia y técnica',
  education_culture: 'Educación y cultura', health: 'Salud', defense: 'Defensa'
};
const capitalExpenditureFunctions = {
  energy: 'Energía', transport: 'Transporte', education: 'Educación',
  housing: 'Vivienda', water: 'Agua', other: 'Otros y fondos fiduciarios'
};

export const sections = [
  {
    id: 'precios', eyebrow: 'PRECIOS', title: 'Inflación', intro: 'Evolución del IPC nacional, los precios mayoristas y el nivel general de precios convertido al dólar oficial.', file: 'inflation.csv',
    warning: 'La inflación en dólares es un cálculo de DatArg: IPC general dividido por el promedio mensual del dólar oficial minorista de venta. Mide precios locales convertidos a esa cotización; no equivale a la inflación de Estados Unidos ni utiliza dólares financieros.',
    charts: [
      { title: 'Inflación mensual', subtitle: 'Variación porcentual contra el mes anterior', unit: '%', defaultRange: '5Y', series: {
        indec_ipc_general_mom: 'Nivel general', indec_ipc_core_mom: 'Núcleo', indec_ipc_regulated_mom: 'Regulados', indec_ipc_seasonal_mom: 'Estacionales', indec_ipim_general_mom: 'Mayorista'
      }},
      { title: 'Inflación interanual', subtitle: 'Variación contra igual mes del año anterior', unit: '%', series: { indec_ipc_general_yoy: 'IPC general', indec_ipc_core_yoy: 'IPC núcleo' }},
      { title: 'Inflación en dólares', subtitle: 'IPC general dividido por el promedio mensual del dólar oficial de venta', file: 'usd_inflation.csv', unit: 'índice', defaultRange: 'ALL', sources: [
        { label: 'INDEC (IPC)', url: 'https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-31' },
        { label: 'ArgentinaDatos (dólar oficial)', url: 'https://api.argentinadatos.com/v1/cotizaciones/dolares/oficial' }
      ], metricToggle: {
        default: 'index',
        labels: { index: 'Índice ene-24=100', mom: 'Variación mensual', yoy: 'Variación interanual' },
        units: { index: 'índice', mom: '%', yoy: '%' },
        seriesByMetric: {
          index: { datarg_usd_inflation_index_jan_2024: 'Nivel de precios en dólares' },
          mom: { datarg_usd_inflation_mom: 'Inflación mensual en dólares' },
          yoy: { datarg_usd_inflation_yoy: 'Inflación interanual en dólares' }
        }
      }, series: { datarg_usd_inflation_index_jan_2024: 'Nivel de precios en dólares' } }
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
    warning: 'Son saldos contables a fin de mes, no flujos de intervención. La cuenta en dólares es un cálculo de DatArg: el saldo oficial en moneda extranjera, que el balance publica convertido a pesos, se divide por el tipo de cambio de valuación del propio BCRA. Una variación puede responder a cobros, pagos de deuda, operaciones con organismos u otros movimientos del Tesoro; por sí sola no prueba una intervención cambiaria.',
    charts: [
      { title: 'Cuenta del Tesoro en pesos', subtitle: 'Saldo de fin de mes y variación mensual', unit: 'M ARS', type: 'bar', defaultRange: '5Y', metricToggle: { default: 'stock', labels: { stock: 'Saldo', change: 'Variación mensual' }, units: { stock: 'M ARS', change: 'M ARS' }, seriesByMetric: { stock: { bcra_treasury_deposits_ars: 'Saldo en pesos' }, change: { bcra_treasury_deposits_ars_monthly_change: 'Variación mensual' } } }, series: { bcra_treasury_deposits_ars: 'Saldo en pesos' } },
      { title: 'Cuenta del Tesoro en dólares', subtitle: 'Saldo estimado de fin de mes y variación mensual', unit: 'USD M', type: 'bar', defaultRange: '5Y', metricToggle: { default: 'stock', labels: { stock: 'Saldo', change: 'Variación mensual' }, units: { stock: 'USD M', change: 'USD M' }, seriesByMetric: { stock: { bcra_treasury_deposits_usd: 'Saldo en dólares' }, change: { bcra_treasury_deposits_usd_monthly_change: 'Variación mensual' } } }, series: { bcra_treasury_deposits_usd: 'Saldo en dólares' } }
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
    id: 'tasas', eyebrow: 'SISTEMA FINANCIERO', title: 'Tasas de interés', intro: 'Tasas bancarias del BCRA y estructura temporal de rendimientos de la deuda en pesos.', file: 'interest_rates.csv',
    charts: [
      { title: 'Tasas mayoristas', subtitle: 'Tasa nominal anual', unit: '% TNA', defaultRange: '5Y', series: { bcra_badlar_private_tna: 'BADLAR', bcra_tamar_private_tna: 'TAMAR' }},
      { title: 'Curvas de deuda en pesos', subtitle: 'TIR efectiva anual por plazo al vencimiento', file: 'yield_curves.csv', renderer: 'yield-curves' }
    ]
  },
  {
    id: 'credito', eyebrow: 'SISTEMA FINANCIERO', title: 'Crédito privado y sector público', intro: 'Préstamos de las entidades financieras al sector privado no financiero y exposición de los bancos al sector público.', file: 'credit.csv',
    warning: 'El índice real deflacta los saldos de fin de mes con el IPC nacional y fija diciembre de 2019 = 100. La vista sobre PIB divide cada saldo por el PIB nominal anualizado de los últimos cuatro trimestres; si todavía no se publicó un trimestre nuevo, mantiene el último denominador disponible. Los préstamos en moneda extranjera están valuados en pesos al tipo de cambio de cada período, por lo que el índice real también puede reflejar cambios de valuación. La exposición pública ampliada excluye Letras y Notas del BCRA.',
    charts: [
      { title: 'Crédito al sector privado no financiero', subtitle: 'Evolución real y profundidad respecto de la economía', unit: 'índice', metricToggle: { default: 'real_index', labels: { real_index: 'Nivel real (dic-19=100)', gdp_ratio: 'Porcentaje del PIB' }, units: { real_index: 'índice', gdp_ratio: '%' }, seriesByMetric: { real_index: { bcra_private_nonfinancial_credit_real_index: 'Sector privado' }, gdp_ratio: { bcra_private_nonfinancial_credit_gdp_ratio: 'Sector privado' } } }, series: { bcra_private_nonfinancial_credit_real_index: 'Sector privado' } },
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
    id: 'deuda', eyebrow: 'FINANZAS PÚBLICAS', title: 'Deuda pública', intro: 'Dos magnitudes separadas: deuda bruta de la Administración Central y pasivos financieros seleccionados del BCRA.', file: 'public_debt.csv', warning: 'Las series no se suman ni equivalen a deuda neta consolidada. Los pasivos seleccionados del BCRA incluyen LEBAC, NOBAC y otras letras emitidas en pesos y moneda extranjera; LELIQ y NOTALIQ; pases pasivos en pesos; y pases pasivos o REPO en dólares con el exterior. Los componentes en pesos se convierten al dólar mayorista de cierre mensual.',
    charts: [
      { title: 'Deuda bruta del Tesoro', subtitle: 'Administración Central; nivel en USD o proporción del PIB', unit: 'USD M', metricToggle: { default: 'usd', labels: { usd: 'Millones de USD', gdp: 'Porcentaje del PIB' }, units: { usd: 'USD M', gdp: '%' }, seriesByMetric: { usd: { mecon_gross_central_government_debt: 'Tesoro' }, gdp: { mecon_gross_central_government_debt_gdp_ratio: 'Tesoro' } } }, series: { mecon_gross_central_government_debt: 'Tesoro' }},
      { title: 'Pasivos seleccionados del BCRA', subtitle: 'Instrumentos remunerados convertidos a USD', unit: 'USD M', series: { bcra_interest_bearing_liabilities: 'BCRA' }}
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
