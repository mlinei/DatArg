from __future__ import annotations

import argparse
import json
from pathlib import Path

from .inflation import PipelineError, run
from .emae import run as run_emae
from .poverty import run as run_poverty
from .trade import run as run_trade
from .gdp import run as run_gdp
from .labor import run as run_labor
from .industry import run as run_industry
from .exchange_rates import run as run_exchange_rates
from .real_exchange_rate import run as run_real_exchange_rate
from .country_risk import run as run_country_risk
from .interest_rates import run as run_interest_rates
from .consolidated_debt import run as run_consolidated_debt
from .public_debt import BCRA_VARIABLES, run as run_public_debt
from .reserves import run as run_reserves
from .wages import run as run_wages
from .markets import run as run_markets
from .net_reserves import run as run_net_reserves
from .fiscal import run as run_fiscal
from .public_investment import run as run_public_investment
from .fx_intervention import run as run_fx_intervention
from .credit import run as run_credit
from .debt_maturities import run as run_debt_maturities
from .yield_curves import run as run_yield_curves
from .usd_inflation import run as run_usd_inflation
from .profit_dividends import run as run_profit_dividends
from .treasury_liquidity import run as run_treasury_liquidity
from .reserve_requirements import run as run_reserve_requirements
from .private_fx_deposits import run as run_private_fx_deposits


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="aed")
    sub = parser.add_subparsers(dest="command", required=True)
    inflation = sub.add_parser("inflation", help="ejecuta IPC e IPIM")
    inflation.add_argument("--root", type=Path, default=Path.cwd())
    inflation.add_argument("--ipc-file", type=Path, help="fuente local para ejecución reproducible")
    inflation.add_argument("--ipim-file", type=Path, help="fuente local para ejecución reproducible")
    emae = sub.add_parser("emae", help="ejecuta EMAE general y sectorial")
    emae.add_argument("--root", type=Path, default=Path.cwd())
    emae.add_argument("--general-file", type=Path, help="libro general local")
    emae.add_argument("--sector-file", type=Path, help="libro sectorial local")
    poverty = sub.add_parser("poverty", help="ejecuta pobreza e indigencia semestral")
    poverty.add_argument("--root", type=Path, default=Path.cwd())
    poverty.add_argument("--source-file", type=Path, help="libro histórico local")
    trade = sub.add_parser("trade", help="ejecuta exportaciones, importaciones y saldo")
    trade.add_argument("--root", type=Path, default=Path.cwd())
    trade.add_argument("--source-file", type=Path, help="JSON histórico local")
    gdp = sub.add_parser("gdp", help="ejecuta PIB trimestral y anual")
    gdp.add_argument("--root", type=Path, default=Path.cwd())
    gdp.add_argument("--original-file", type=Path, help="libro original local")
    gdp.add_argument("--sa-file", type=Path, help="libro desestacionalizado local")
    labor = sub.add_parser("labor", help="ejecuta tasas de actividad, empleo y desocupación")
    labor.add_argument("--root", type=Path, default=Path.cwd())
    labor.add_argument("--source-file", type=Path, help="libro histórico local")
    industry = sub.add_parser("industry", help="ejecuta IPI manufacturero por división")
    industry.add_argument("--root", type=Path, default=Path.cwd())
    industry.add_argument("--source-file", type=Path, help="libro histórico local")
    fx = sub.add_parser("exchange-rates", help="ejecuta dólar oficial, blue, MEP y CCL")
    fx.add_argument("--root", type=Path, default=Path.cwd())
    for house in ("oficial", "blue", "bolsa", "contadoconliqui"):
        fx.add_argument(f"--{house}-file", type=Path)
    real_fx = sub.add_parser("real-exchange-rate", help="ejecuta ITCRM y bilaterales reales del BCRA")
    real_fx.add_argument("--root", type=Path, default=Path.cwd())
    real_fx.add_argument("--source-file", type=Path, help="libro histórico local")
    risk = sub.add_parser("country-risk", help="ejecuta la evolución del riesgo país")
    risk.add_argument("--root", type=Path, default=Path.cwd())
    risk.add_argument("--source-file", type=Path)
    rates = sub.add_parser("interest-rates", help="ejecuta TAMAR y BADLAR del BCRA")
    rates.add_argument("--root", type=Path, default=Path.cwd())
    for variable_id in (7, 35, 44, 45): rates.add_argument(f"--variable-{variable_id}-file", type=Path)
    reserve_requirements = sub.add_parser("reserve-requirements", help="ejecuta la exigencia promedio de encajes del BCRA")
    reserve_requirements.add_argument("--root", type=Path, default=Path.cwd())
    reserve_requirements.add_argument("--source-file", type=Path, help="archivo din1_ser local")
    intervention = sub.add_parser("fx-intervention", help="ejecuta intervención cambiaria diaria del BCRA")
    intervention.add_argument("--root", type=Path, default=Path.cwd())
    intervention.add_argument("--source-file", type=Path)
    intervention.add_argument("--futures-dir", type=Path, help="directorio con planillas mensuales NEDD")
    dividends = sub.add_parser("profit-dividends", help="ejecuta giros de utilidades y dividendos al exterior")
    dividends.add_argument("--root", type=Path, default=Path.cwd())
    dividends.add_argument("--source-file", type=Path, help="anexo estadístico local del mercado de cambios")
    treasury_liquidity = sub.add_parser("treasury-liquidity", help="ejecuta depósitos del Tesoro en el BCRA")
    treasury_liquidity.add_argument("--root", type=Path, default=Path.cwd())
    treasury_liquidity.add_argument("--balance-file", type=Path, help="archivo mensual din1_ser local")
    treasury_liquidity.add_argument("--valuation-fx-file", type=Path, help="archivo diario din2_ser local")
    treasury_liquidity.add_argument("--daily-balance-file", type=Path, help="planilla diaria diar_bas.xls local")
    credit = sub.add_parser("credit", help="ejecuta crédito privado y exposición al sector público")
    credit.add_argument("--root", type=Path, default=Path.cwd())
    credit.add_argument("--private-file", type=Path)
    credit.add_argument("--public-file", type=Path)
    credit.add_argument("--securities-file", type=Path)
    debt = sub.add_parser("consolidated-debt", help="ejecuta deuda neta consolidada estimada")
    debt.add_argument("--root", type=Path, default=Path.cwd())
    debt.add_argument("--source-file", type=Path, help="informe PDF local")
    public_debt = sub.add_parser("public-debt", help="ejecuta deuda del Tesoro y tres medidas de pasivos del BCRA")
    public_debt.add_argument("--root", type=Path, default=Path.cwd())
    public_debt.add_argument("--treasury-file", type=Path, help="XLSX mensual local")
    public_debt.add_argument("--quarterly-file", type=Path, help="XLSX trimestral con indicadores de sostenibilidad")
    public_debt.add_argument("--daily-liabilities-file", type=Path, help="planilla diaria diar_bas.xls local")
    public_debt.add_argument("--weekly-balance-file", type=Path, help="balance semanal resumido local")
    for variable_id in BCRA_VARIABLES: public_debt.add_argument(f"--variable-{variable_id}-file", type=Path)
    reserves = sub.add_parser("reserves", help="ejecuta reservas internacionales brutas del BCRA")
    reserves.add_argument("--root", type=Path, default=Path.cwd())
    reserves.add_argument("--source-file", type=Path)
    private_fx_deposits = sub.add_parser("private-fx-deposits", help="ejecuta depósitos privados en dólares del BCRA")
    private_fx_deposits.add_argument("--root", type=Path, default=Path.cwd())
    private_fx_deposits.add_argument("--source-file", type=Path)
    net_reserves = sub.add_parser("net-reserves", help="reconstruye reservas internacionales netas")
    net_reserves.add_argument("--root", type=Path, default=Path.cwd())
    net_reserves.add_argument("--weekly-file", type=Path)
    net_reserves.add_argument("--flow-file", type=Path)
    net_reserves.add_argument("--cny-file", type=Path)
    net_reserves.add_argument("--usd-file", type=Path)
    wages = sub.add_parser("wages", help="ejecuta salarios nominales y reales por sector")
    wages.add_argument("--root", type=Path, default=Path.cwd())
    wages.add_argument("--source-file", type=Path)
    markets = sub.add_parser("markets", help="ejecuta S&P Merval convertido por dólar MEP")
    markets.add_argument("--root", type=Path, default=Path.cwd())
    markets.add_argument("--source-file", type=Path)
    fiscal = sub.add_parser("fiscal", help="ejecuta recaudación y resultados fiscales del SPN")
    fiscal.add_argument("--root", type=Path, default=Path.cwd())
    fiscal.add_argument("--tax-file", type=Path, action="append", help="planilla de recaudación local; repetible")
    fiscal.add_argument("--fiscal-file", type=Path, action="append", help="planilla o ZIP fiscal local; repetible")
    fiscal.add_argument("--refresh-history", action="store_true", help="reconstruye el historial oficial desde 2017")
    public_investment = sub.add_parser("public-investment", help="ejecuta inversión pública y gastos de capital")
    public_investment.add_argument("--root", type=Path, default=Path.cwd())
    public_investment.add_argument("--source-file", type=Path, help="planilla oficial local")
    maturities = sub.add_parser("debt-maturities", help="ejecuta el cronograma proyectado de vencimientos del Tesoro")
    maturities.add_argument("--root", type=Path, default=Path.cwd())
    maturities.add_argument("--source-file", type=Path, help="libro trimestral oficial local")
    yield_curves = sub.add_parser("yield-curves", help="calcula curvas nominal, CER y breakeven con fuentes públicas")
    yield_curves.add_argument("--root", type=Path, default=Path.cwd())
    yield_curves.add_argument("--source-file", type=Path, help="cierre normalizado alternativo con precios y flujos")
    usd_inflation = sub.add_parser("usd-inflation", help="calcula inflación en dólares desde IPC y dólar oficial")
    usd_inflation.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    try:
        if args.command == "inflation":
            result = run(args.root.resolve(), args.ipc_file, args.ipim_file)
        elif args.command == "emae":
            result = run_emae(args.root.resolve(), args.general_file, args.sector_file)
        elif args.command == "poverty":
            result = run_poverty(args.root.resolve(), args.source_file)
        elif args.command == "trade":
            result = run_trade(args.root.resolve(), args.source_file)
        elif args.command == "gdp":
            result = run_gdp(args.root.resolve(), args.original_file, args.sa_file)
        elif args.command == "labor":
            result = run_labor(args.root.resolve(), args.source_file)
        elif args.command == "industry":
            result = run_industry(args.root.resolve(), args.source_file)
        elif args.command == "exchange-rates":
            files = {house: getattr(args, f"{house}_file") for house in ("oficial", "blue", "bolsa", "contadoconliqui")}
            result = run_exchange_rates(args.root.resolve(), files)
        elif args.command == "real-exchange-rate":
            result = run_real_exchange_rate(args.root.resolve(), args.source_file)
        elif args.command == "country-risk":
            result = run_country_risk(args.root.resolve(), args.source_file)
        elif args.command == "interest-rates":
            files = {i: getattr(args, f"variable_{i}_file") for i in (7, 35, 44, 45)}
            result = run_interest_rates(args.root.resolve(), files)
        elif args.command == "reserve-requirements":
            result = run_reserve_requirements(args.root.resolve(), args.source_file)
        elif args.command == "fx-intervention":
            result = run_fx_intervention(args.root.resolve(), args.source_file, args.futures_dir)
        elif args.command == "profit-dividends":
            result = run_profit_dividends(args.root.resolve(), args.source_file)
        elif args.command == "treasury-liquidity":
            result = run_treasury_liquidity(
                args.root.resolve(), args.balance_file, args.valuation_fx_file, args.daily_balance_file,
            )
        elif args.command == "credit":
            result = run_credit(args.root.resolve(), args.private_file, args.public_file, args.securities_file)
        elif args.command == "consolidated-debt":
            result = run_consolidated_debt(args.root.resolve(), args.source_file)
        elif args.command == "public-debt":
            files = {i: getattr(args, f"variable_{i}_file") for i in BCRA_VARIABLES}
            result = run_public_debt(
                args.root.resolve(), args.treasury_file, files, args.quarterly_file,
                args.daily_liabilities_file, args.weekly_balance_file,
            )
        elif args.command == "reserves":
            result = run_reserves(args.root.resolve(), args.source_file)
        elif args.command == "private-fx-deposits":
            result = run_private_fx_deposits(args.root.resolve(), args.source_file)
        elif args.command == "net-reserves":
            result = run_net_reserves(args.root.resolve(), args.weekly_file, args.flow_file, args.cny_file, args.usd_file)
        elif args.command == "wages":
            result = run_wages(args.root.resolve(), args.source_file)
        elif args.command == "markets":
            result = run_markets(args.root.resolve(), args.source_file)
        elif args.command == "fiscal":
            result = run_fiscal(args.root.resolve(), args.tax_file, args.fiscal_file, args.refresh_history)
        elif args.command == "public-investment":
            result = run_public_investment(args.root.resolve(), args.source_file)
        elif args.command == "debt-maturities":
            result = run_debt_maturities(args.root.resolve(), args.source_file)
        elif args.command == "yield-curves":
            result = run_yield_curves(args.root.resolve(), args.source_file)
        else:
            result = run_usd_inflation(args.root.resolve())
    except PipelineError as exc:
        parser.exit(1, f"error: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0
