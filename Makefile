.PHONY: install inflation emae poverty trade gdp labor industry exchange-rates country-risk interest-rates test

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

industry:
	python3 -m argentina_economic_data industry

exchange-rates:
	python3 -m argentina_economic_data exchange-rates

country-risk:
	python3 -m argentina_economic_data country-risk

interest-rates:
	python3 -m argentina_economic_data interest-rates

test:
	python3 -m unittest discover -s tests -v
