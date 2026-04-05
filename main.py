import flet as ft
import pandas as pd
import os

def load_data(filename):
    base_path = os.path.dirname(__file__)
    full_path = os.path.join(base_path, filename)
    if os.path.exists(full_path):
        try:
            df = pd.read_csv(full_path, sep=';', header=None, skiprows=2, encoding='utf-8-sig')
            df.set_index(0, inplace=True)
            res_list = ['0-0', '1-0', '0-1', '1-1', '2-0', '0-2', '3-0', '0-3', '2-1', '1-2', '3-1', '1-3', '2-2']
            df.columns = [f"PUNTA_{r}" for r in res_list] + [f"BANCA_{r}" for r in res_list]
            for col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
            return df
        except: return None
    return None

def main(page: ft.Page):
    page.title = "TYPO HT-PRO"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0a0e14"
    # ATTIVIAMO LO SCROLL SU TUTTA LA PAGINA
    page.scroll = ft.ScrollMode.ALWAYS 
    page.padding = 10

    df_bibbia = load_data('database_bibbia.csv')

    # --- ELEMENTI UI CON DIMENSIONI RIDOTTE PER MOBILE ---
    dd_camp = ft.Dropdown(
        label="CAMPIONATO",
        options=[ft.dropdown.Option(c) for c in sorted(df_bibbia.index.tolist())] if df_bibbia is not None else [],
        label_style=ft.TextStyle(size=12),
        text_size=14,
        height=55
    )

    in_casa = ft.TextField(label="GOL CASA", value="0", expand=1, keyboard_type="number", text_align="center", height=55)
    in_ospite = ft.TextField(label="GOL OSPITE", value="0", expand=1, keyboard_type="number", text_align="center", height=55)
    
    in_punta = ft.TextField(label="PUNTA", expand=1, keyboard_type="number", color="#448aff", height=55)
    in_banca = ft.TextField(label="BANCA", expand=1, keyboard_type="number", color="#ff5252", height=55)

    in_bank = ft.TextField(label="BANK €", value="100", expand=1, keyboard_type="number", height=55, text_size=12)
    in_stake = ft.TextField(label="STAKE %", value="5", expand=1, keyboard_type="number", height=55, text_size=12)
    in_comm = ft.TextField(label="COMM %", value="4.5", expand=1, keyboard_type="number", height=55, text_size=12)

    col_res = ft.Column(spacing=10, width=page.width)

    def analizza_click(e):
        col_res.controls.clear()
        if not dd_camp.value or not in_punta.value or not in_banca.value:
            page.snack_bar = ft.SnackBar(ft.Text("Mancano dati!"))
            page.snack_bar.open = True
            page.update()
            return

        try:
            v_p = float(in_punta.value.replace(",", "."))
            v_b = float(in_banca.value.replace(",", "."))
            bank = float(in_bank.value.replace(",", "."))
            stake_p = float(in_stake.value.replace(",", "."))
            comm = float(in_comm.value.replace(",", ".")) / 100
            c_score = f"{in_casa.value}-{in_ospite.value}"
            
            if dd_camp.value in df_bibbia.index:
                lim_p = df_bibbia.loc[dd_camp.value, f"PUNTA_{c_score}"]
                lim_b = df_bibbia.loc[dd_camp.value, f"BANCA_{c_score}"]
                
                ok_p = v_p < lim_p
                ok_b = v_b > lim_b
                
                rischio = bank * (stake_p / 100)
                prof_p = (rischio * (v_p - 1)) * (1 - comm)
                lay_stake = rischio / (v_b - 1)
                prof_b = lay_stake * (1 - comm)

                col_res.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(f"TARGET: OVER {int(in_casa.value)+int(in_ospite.value)+0.5}", weight="bold", color="#64ffda"),
                            ft.Row([ft.Icon(ft.Icons.CHECK if ok_p else ft.Icons.CLOSE, color="green" if ok_p else "red", size=20), ft.Text(f"PUNTA (< {lim_p})")]),
                            ft.Row([ft.Icon(ft.Icons.CHECK if ok_b else ft.Icons.CLOSE, color="green" if ok_b else "red", size=20), ft.Text(f"BANCA (> {lim_b})")]),
                            ft.Divider(),
                            ft.Text(f"NETTO PUNTA: € {prof_p:.2f}", color="green" if ok_p else "white", size=15, weight="bold"),
                            ft.Text(f"NETTO BANCA: € {prof_b:.2f}", color="green" if ok_b else "white", size=15, weight="bold"),
                        ], spacing=5),
                        padding=15, bgcolor="#16213e", border_radius=10
                    )
                )
            page.update()
        except Exception as ex:
            col_res.controls.append(ft.Text(f"Errore: {ex}", color="red"))
            page.update()

    btn = ft.ElevatedButton(
        content=ft.Row([ft.Icon(ft.Icons.SEARCH), ft.Text("ANALIZZA MATCH", weight="bold")], alignment="center"),
        on_click=analizza_click, height=50, style=ft.ButtonStyle(bgcolor="#007bff", color="white", shape=ft.RoundedRectangleBorder(radius=8))
    )

    # COSTRUIAMO IL LAYOUT
    page.add(
        ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.ANALYTICS, color="#64ffda", size=30),
                ft.Text("TYPO HT-PRO", size=22, weight="black"),
            ], alignment="center"),
            
            ft.Divider(height=5),
            dd_camp,
            ft.Row([in_casa, in_ospite], spacing=10),
            
            ft.Text("QUOTE ATTUALI", size=11, color="#888888", weight="bold"),
            ft.Row([in_punta, in_banca], spacing=10),
            
            ft.Text("MONEY MANAGEMENT", size=11, color="#888888", weight="bold"),
            ft.Row([in_bank, in_stake, in_comm], spacing=5),
            
            btn,
            col_res,
            ft.Container(height=50) # Spazio extra in fondo per non coprire col tasto
        ], spacing=15)
    )

ft.app(target=main)
