"""
Author : Abhishek Yadav
Description: Automation Scraping Test
Version : 1.0
Date: 21 August 2023
Azure Ticket Link : https://dev.azure.com/ShorthillsCampus/Training%20Batch%202023/_workitems/edit/3245

This script performs web scraping using Selenium to extract data from the U.S. Census Bureau's QuickFacts website.
It navigates through specified county and state combinations to retrieve population data and other statistics.

Required Libraries:
- os: Provides a way to interact with the operating system.
- selenium: A web automation framework used to control web browsers.
- pandas: A data manipulation library.
- json: For handling JSON data.
"""

import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import json

class CensusScraper:
    def __init__(self, chrome_driver_path):
        self.chrome_driver_path = chrome_driver_path
        self.driver = self.setup_driver()

    def setup_driver(self):
        # Set up the Chrome WebDriver
        service_obj = Service(self.chrome_driver_path)
        driver = webdriver.Chrome(service=service_obj)
        return driver

    def remove_emoji(self, input_string):
        # Remove emojis from the input string
        last_newline_index = input_string.rfind('\n')
        extracted_string = input_string[last_newline_index + 1:] if last_newline_index != -1 else input_string
        return extracted_string

    def scrape_table_data(self, table):
        # Scrape data from a table on the webpage
        table_bodies = table.find_elements(By.TAG_NAME, 'tbody')
        state_data = []

        for tbody in table_bodies:
            table_heads = tbody.find_elements(By.TAG_NAME, 'th')
            table_rows = tbody.find_elements(By.TAG_NAME, 'tr')

            if table_heads:
                parameter = table_heads[0].text
                fields = []

                for table_row in table_rows:
                    table_data = table_row.find_elements(By.TAG_NAME, 'td')

                    if len(table_data) == 2:
                        parameter_type = table_data[0].text
                        field = {
                            parameter_type: self.remove_emoji(table_data[1].text)
                        }
                        fields.append(field)

                parameter_fields = {
                    parameter: fields
                }
                state_data.append(parameter_fields)
                
        return state_data

    def navigate_to_county_state(self, county_name, state_name):
        # Navigate to a specified county and state combination
        wait = WebDriverWait(self.driver, 10)
        url = f"https://www.census.gov/quickfacts/fact/table/{county_name}county{state_name}/PST045222"
        self.driver.get(url)

        tables = wait.until(EC.visibility_of_all_elements_located((By.TAG_NAME, 'table')))
        state_data = []

        for idx, table in enumerate(tables):
            if idx != 0:
                state_data.extend(self.scrape_table_data(table))

        complete_state_data = {
            "state": state_name,
            "county": county_name,
            "result_url": url,
            "data": state_data
        }

        return complete_state_data

    def get_all_data(self, csv_file_path, json_file_path):
        # Get data for all county and state combinations
        self.driver.maximize_window()
        data = pd.read_csv(csv_file_path, usecols=[0, 1])
        unique_data = data.drop_duplicates()

        final_data = []
        for _, row in unique_data.iterrows():
            county = row.iloc[1].lower()
            state = row.iloc[0].lower()

            final_data.append(self.navigate_to_county_state(county, state))

        final_data_json = json.dumps(final_data, indent=4)

        
        with open(json_file_path, "w") as json_file:
            json_file.write(final_data_json)

chrome_driver_path = os.getcwd() + '/drivers/chromedriver'    
json_file_path = os.getcwd() + '/census_results.json'
csv_file_path = os.getcwd() + '/census_geo_sheet.csv'

# Create an instance of the CensusScraper class
scraper = CensusScraper(chrome_driver_path)
# Initiate the data extraction process
scraper.get_all_data(csv_file_path, json_file_path)
