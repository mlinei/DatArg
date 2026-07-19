.PHONY: install inflation emae poverty trade gdp labor wages industry exchange-rates markets reserves net-reserves country-risk interest-rates fiscal public-investment test

install:
	python3 -m pip install -e .

inflation:
	python3 -m argentina_economic_data inflation

emae:
	python3 -m argentina_economic_data emae

poverty:
	python3 -m argentina_economic_data poverty

trade:
	python3 -m argentina_economic_data trade

gdp:
	python3 -m argentina_economic_data gdp

labor:
	python3 -m argentina_economic_data labor

wages:
	python3 -m argentina_economic_data wages

industry:
	python3 -m argentina_economic_data industry

exchange-rates:
	python3 -m argentina_economic_data exchange-rates

markets:
	python3 -m argentina_economic_data markets

reserves:
	python3 -m argentina_economic_data reserves

net-reserves:
	python3 -m argentina_economic_data net-reserves

country-risk:
	python3 -m argentina_economic_data country-risk

interest-rates:
	python3 -m argentina_economic_data interest-rates

fiscal:
	python3 -m argentina_economic_data fiscal

public-investment:
	python3 -m argentina_economic_data public-investment

test:
	python3 -m unittest discover -s tests -v
