import pandas as pd
import numpy as np
import re

def clean_and_convert_car_data(input_csv_filename="Complete_ICE_EV_car_data.csv",
                               output_csv_filename="Complete_ICE_EV_car_data_repair.csv"):
    """
    Načte data o autech z CSV, očistí specifikované sloupce (extrahuje text před první mezerou),
    převede je na číselné hodnoty, nahradí chybějící/neplatné hodnoty nulami
    a uloží je s desetinnou čárkou do nového CSV souboru.
    """
    print(f"Běží skript pro čištění dat. Aktuální čas: {pd.Timestamp.now()}")
    try:
        print("Pokusím se načíst CSV s 'python' engine, oddělovačem ';' a 'on_bad_lines='warn' pro robustnost...")
        # ZMĚNA ZDE: sep=';' pro správné načtení souboru se středníkem jako oddělovačem
        df = pd.read_csv(input_csv_filename, engine='python', on_bad_lines='warn', quotechar='"', sep=';')
        print(f"Soubor '{input_csv_filename}' úspěšně načten. Počet řádků: {len(df)}")
        print(f"Původní sloupce a jejich datové typy (prvních 5):\n{df.dtypes.head(5)}\n")
        print(f"Prvních 3 řádky (pro ověření načtení):\n{df.head(3)}\n")

        # REALNÉ NÁZVY SLOUPCŮ Z CSV - BEZ JEDNOTEK V HRANATÝCH ZÁVORKÁCH
        # Seznamy sloupců, které se mají zpracovat jako float
        columns_to_process_float = [
            "Braking Distance (100-0 km/h)", "Braking Distance (200-0 km/h)",
            "Acceleration (0-100 km/h)", "Acceleration (0-100 km/h)_CNG",
            "Acceleration (0-100 km/h)_Ethanol___E85", "Acceleration (0-100 km/h)_LPG",
            "Acceleration (0-200 km/h)", "Acceleration (0-300 km/h)",
            "Acceleration (0-60 mph)", "Acceleration (0-60 mph)_Calculated_by_Auto_Datanet",
            "Acceleration (0-62 mph)", "AdBlue_tank", "All_electric_range",
            "All_electric_range_CLTC", "All_electric_range_EPA", "All_electric_range_NEDC",
            "All_electric_range_NEDC,_WLTP_equivalent", "All_electric_range_WLTC",
            "All_electric_range_WLTP", "Average_Energy_consumption",
            "Average_Energy_consumption_CLTC", "Average_Energy_consumption_EPA",
            "Average_Energy_consumption_NEDC", "Average_Energy_consumption_NEDC,_WLTP_equivalent",
            "Average_Energy_consumption_WLTC", "Average_Energy_consumption_WLTP",
            "Battery_voltage", "Battery_weight", "CNG_cylinder_capacity",
            "CO_2_emissions", "CO_2_emissions_CNG", "CO_2_emissions_CNG_NEDC",
            "CO_2_emissions_CNG_NEDC,_WLTP_equivalent", "CO_2_emissions_CNG_WLTP",
            "CO_2_emissions_EPA", "CO_2_emissions_Ethanol___E85",
            "CO_2_emissions_Ethanol___E85_NEDC", "CO_2_emissions_LPG",
            "CO_2_emissions_LPG_NEDC", "CO_2_emissions_LPG_NEDC,_WLTP_equivalent",
            "CO_2_emissions_LPG_WLTP", "CO_2_emissions_NEDC",
            "CO_2_emissions_NEDC,_WLTP_equivalent", "CO_2_emissions_WLTP",
            "Combined_fuel_consumption_WLTP", "Combined_fuel_consumption_WLTP_CNG",
            "Combined_fuel_consumption_WLTP_LPG", "Compression_ratio",
            "Cylinder_Bore", "Electric_motor_Torque", "Electric_motor_power",
            "Engine_displacement", "Engine_oil_capacity",
            "Fuel_consumption_at_Low_speed_WLTP", "Fuel_consumption_at_Low_speed_WLTP_CNG",
            "Fuel_consumption_at_Low_speed_WLTP_LPG", "Fuel_consumption_at_Medium_speed_WLTP",
            "Fuel_consumption_at_Medium_speed_WLTP_CNG", "Fuel_consumption_at_Medium_speed_WLTP_LPG",
            "Fuel_consumption_at_high_speed_WLTP", "Fuel_consumption_at_high_speed_WLTP_CNG",
            "Fuel_consumption_at_high_speed_WLTP_LPG", "Fuel_consumption_at_very_high_speed_WLTP",
            "Fuel_consumption_at_very_high_speed_WLTP_CNG", "Fuel_consumption_at_very_high_speed_WLTP_LPG",
            "Fuel_consumption_economy___combined", "Fuel_consumption_economy___combined_CLTC",
            "Fuel_consumption_economy___combined_CNG", "Fuel_consumption_economy___combined_CNG_NEDC",
            "Fuel_consumption_economy___combined_CNG_NEDC,_WLTP_equivalent", "Fuel_consumption_economy___combined_EPA",
            "Fuel_consumption_economy___combined_Ethanol___E85", "Fuel_consumption_economy___combined_Ethanol___E85_NEDC",
            "Fuel_consumption_economy___combined_LPG", "Fuel_consumption_economy___combined_LPG_NEDC",
            "Fuel_consumption_economy___combined_LPG_NEDC,_WLTP_equivalent", "Fuel_consumption_economy___combined_NEDC",
            "Fuel_consumption_economy___combined_NEDC,_WLTP_equivalent", "Fuel_consumption_economy___combined_WLTC",
            "Fuel_consumption_economy___extra_urban", "Fuel_consumption_economy___extra_urban_CNG",
            "Fuel_consumption_economy___extra_urban_CNG_NEDC", "Fuel_consumption_economy___extra_urban_CNG_NEDC,_WLTP_equivalent",
            "Fuel_consumption_economy___extra_urban_EPA", "Fuel_consumption_economy___extra_urban_Ethanol___E85",
            "Fuel_consumption_economy___extra_urban_Ethanol___E85_NEDC", "Fuel_consumption_economy___extra_urban_LPG",
            "Fuel_consumption_economy___extra_urban_LPG_NEDC", "Fuel_consumption_economy___extra_urban_LPG_NEDC,_WLTP_equivalent",
            "Fuel_consumption_economy___extra_urban_NEDC", "Fuel_consumption_economy___extra_urban_NEDC,_WLTP_equivalent",
            "Fuel_consumption_economy___urban", "Fuel_consumption_economy___urban_CNG",
            "Fuel_consumption_economy___urban_CNG_NEDC", "Fuel_consumption_economy___urban_CNG_NEDC,_WLTP_equivalent",
            "Fuel_consumption_economy___urban_EPA", "Fuel_consumption_economy___urban_Ethanol___E85",
            "Fuel_consumption_economy___urban_Ethanol___E85_NEDC", "Fuel_consumption_economy___urban_LPG",
            "Fuel_consumption_economy___urban_LPG_NEDC", "Fuel_consumption_economy___urban_LPG_NEDC,_WLTP_equivalent",
            "Fuel_consumption_economy___urban_NEDC", "Fuel_consumption_economy___urban_NEDC,_WLTP_equivalent",
            "Fuel_tank_capacity", "Fuel_tank_capacity_LPG", "Gross_battery_capacity",
            "Net_usable_battery_capacity", "Recuperation_output", "System_power",
            "System_torque", "Power", "Power_CNG", "Power_Ethanol___E85", "Power_LPG",
            "Power_per_litre", "Power_per_litre_CNG", "Power_per_litre_Ethanol___E85",
            "Power_per_litre_LPG", "Torque", "Torque_CNG", "Torque_Ethanol___E85", "Torque_LPG",
            "Trunk_boot_space___maximum", "Trunk_boot_space___minimum",
            "Weight_to_power_ratio", "Weight_to_torque_ratio", "Max_weight",
            "Approach_angle", "Climb_angle", "Departure_angle", "Front_overhang",
            "Front_track", "Height", "Kerb_Weight", "Length", "Max_load",
            "Max_roof_load", "Minimum_turning_circle_turning_diameter",
            "Permitted_towbar_download", "Permitted_trailer_load_with_brakes_12%",
            "Permitted_trailer_load_with_brakes_8%", "Permitted_trailer_load_without_brakes",
            "Piston_Stroke", "Ramp_over_brakeover_angle", "Rear_Back_track",
            "Rear_overhang", "Ride_height_ground_clearance", "Wading_depth",
            "Wheelbase", "Width", "Width_including_mirrors", "Width_with_mirrors_folded",
            "Max_speed_electric", "Maximum_engine_speed", "Maximum_revolutions_of_the_electric_motor",
            "Maximum_speed", "Maximum_speed_CNG", "Maximum_speed_Ethanol___E85", "Maximum_speed_LPG",
        ]

        # Sloupce, které mají být celá čísla
        columns_to_convert_to_int = [
            "Doors", "End_of_production", "Number_of_cylinders",
            "Number_of_valves_per_cylinder", "Seats", "Start_of_production",
        ]

        # Sloupce pro podrobné debugování (můžeš je změnit)
        debug_columns = ["Acceleration (0-100 km/h)", "AdBlue_tank", "Weight_to_power_ratio", "Cylinder_Bore"]
        
        print("\nSpouštím čištění a konverzi číselných sloupců (float)...")
        for col_name in columns_to_process_float:
            if col_name in df.columns:
                is_debug_col = col_name in debug_columns
                example_value = None
                if not df[col_name].empty:
                    example_value = df[col_name].iloc[0]
                
                if is_debug_col:
                    print(f"\n--- DEBUG pro sloupec '{col_name}' ---")
                    print(f"Původní hodnota (první): '{example_value}'")
                
                # 1. Převedeme na string a odstraníme mezery
                temp_series = df[col_name].astype(str).str.strip()
                if is_debug_col:
                    print(f"Po .astype(str).str.strip(): '{temp_series.iloc[0]}'")

                # 2. Rozdělíme u první mezery a vezmeme první část (Power Query logika)
                temp_series = temp_series.str.split(' ', n=1).str[0]
                if is_debug_col:
                    print(f"Po .str.split(' ', n=1).str[0]: '{temp_series.iloc[0]}'")

                # 3. Nahradíme desetinné čárky tečkami pro pd.to_numeric (pokud nějaké jsou)
                temp_series = temp_series.str.replace(',', '.')
                if is_debug_col:
                    print(f"Po .str.replace(',', '.'): '{temp_series.iloc[0]}'")

                # 4. Převedeme na číslo (NaN pro chyby)
                df[col_name] = pd.to_numeric(temp_series, errors='coerce')
                if is_debug_col:
                    print(f"Po pd.to_numeric(..., errors='coerce'): '{df[col_name].iloc[0]}'")

                # 5. Nahradíme NaN nulou
                df[col_name] = df[col_name].fillna(0)
                if is_debug_col:
                    print(f"Po .fillna(0): '{df[col_name].iloc[0]}'")
                    print(f"Konečný typ sloupce: {df[col_name].dtype}")
                
            else:
                print(f"Upozornění: Sloupec '{col_name}' pro float konverzi nebyl nalezen a bude přeskočen.")

        print("\nSpouštím čištění a konverzi číselných sloupců (int)...")
        columns_for_int_only = [col for col in columns_to_convert_to_int if col not in columns_to_process_float]

        for col_name in columns_for_int_only:
            if col_name in df.columns:
                is_debug_col = col_name in debug_columns
                example_value = None
                if not df[col_name].empty:
                    example_value = df[col_name].iloc[0]
                
                if is_debug_col:
                    print(f"\n--- DEBUG pro sloupec '{col_name}' ---")
                    print(f"Původní hodnota (první): '{example_value}'")

                temp_series = df[col_name].astype(str).str.strip()
                if is_debug_col:
                    print(f"Po .astype(str).str.strip(): '{temp_series.iloc[0]}'")

                temp_series = temp_series.str.split(' ', n=1).str[0]
                if is_debug_col:
                    print(f"Po .str.split(' ', n=1).str[0]: '{temp_series.iloc[0]}'")

                temp_series = temp_series.str.replace(',', '.')
                if is_debug_col:
                    print(f"Po .str.replace(',', '.'): '{temp_series.iloc[0]}'")

                df[col_name] = pd.to_numeric(temp_series, errors='coerce')
                if is_debug_col:
                    print(f"Po pd.to_numeric(..., errors='coerce'): '{df[col_name].iloc[0]}'")

                df[col_name] = df[col_name].fillna(0).astype(int) 
                if is_debug_col:
                    print(f"Po .fillna(0).astype(int): '{df[col_name].iloc[0]}'")
                    print(f"Konečný typ sloupce: {df[col_name].dtype}")
            else:
                print(f"Upozornění: Sloupec '{col_name}' pro int konverzi nebyl nalezen a bude přeskočen.")

        # Finální převod desetinné tečky na čárku pro číselné sloupce před uložením
        print("\nPřevádím desetinné tečky na čárky pro export...")
        for col in df.select_dtypes(include=[np.number]).columns:
            if df[col].dtype == 'float64':
                # Formátování na string s desetinnou čárkou pro float
                # Používáme pd.Series.round(decimals=N) před formátováním, aby se omezil počet desetinných míst
                # nebo můžete použít f-string formátování jako '{:.1f}'.format(x) pro jedno desetinné místo
                df[col] = df[col].apply(lambda x: str(round(x, 2)).replace('.', ',')) # Zaokrouhlení na 2 desetinná místa
            elif df[col].dtype == 'int64':
                df[col] = df[col].astype(str) # Celá čísla jako string

        print(f"\nKonečné datové typy upravených sloupců (prvních 5):\n{df.dtypes.head(5)}\n")

        # Uložení upraveného DataFrame do nového CSV souboru
        df.to_csv(output_csv_filename, index=False, encoding='utf-8')
        print(f"Data byla úspěšně upravena a uložena do: {output_csv_filename}")
        print(f"Dokončeno. Aktuální čas: {pd.Timestamp.now()}")

    except FileNotFoundError:
        print(f"CHYBA: Soubor '{input_csv_filename}' nebyl nalezen ve stejné složce jako skript.")
        print("Ujistěte se, že název souboru je správný a je ve stejné složce.")
    except pd.errors.ParserError as pe:
        print(f"CHYBA PARSOVÁNÍ CSV: {pe}")
        print("Pravděpodobná příčina: Nesrovnalost v počtu sloupců nebo formátování oddělovačů v CSV.")
        print("Zkuste otevřít soubor v textovém editoru a zkontrolujte chyby (např. neuzavřené uvozovky, extra oddělovače).")
    except Exception as e:
        print(f"Při zpracování dat došlo k neočekávané chybě: {e}")

# --- Spuštění skriptu ---
if __name__ == "__main__":
    clean_and_convert_car_data()