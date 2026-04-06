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
    page.title = "TYPO HT-PRO MOBILE"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0a0e14"
    page.scroll = ft.ScrollMode.AUTO 
    page.padding = 15

    df_bibbia = load_data('database_bibbia.csv')

    # --- ELEMENTI UI ---
    dd_camp = ft.Dropdown(
        label="CAMPIONATO",
        options=[ft.dropdown.Option(c) for c in sorted(df_bibbia.index.tolist())] if df_bibbia is not None else [],
        text_size=14, height=60, border_color="#448aff"
    )

    in_casa = ft.TextField(label="GOL CASA", value="0", expand=1, keyboard_type="number", text_align="center")
    in_ospite = ft.TextField(label="GOL OSPITE", value="0", expand=1, keyboard_type="number", text_align="center")
    
    in_punta = ft.TextField(label="QUOTA PUNTA", expand=1, keyboard_type="number", color="#448aff", border_color="#448aff")
    in_banca = ft.TextField(label="QUOTA BANCA", expand=1, keyboard_type="number", color="#ff5252", border_color="#ff5252")

    in_bank = ft.TextField(label="BANK €", value="100", expand=1, keyboard_type="number")
    in_stake = ft.TextField(label="STAKE %", value="5", expand=1, keyboard_type="number")
    in_comm = ft.TextField(label="COMM %", value="4.5", expand=1, keyboard_type="number")

    col_res = ft.Column(spacing=10)

    def analizza_click(e):
        col_res.controls.clear()
        if not dd_camp.value or not in_punta.value or not in_banca.value:
            page.snack_bar = ft.SnackBar(ft.Text("Inserisci tutti i dati obbligatori!"))
            page.snack_bar.open = True
            page.update()
            return

        try:
            # Parsing dati
            v_p = float(in_punta.value.replace(",", "."))
            v_b = float(in_banca.value.replace(",", "."))
            bank = float(in_bank.value.replace(",", "."))
            stake_perc = float(in_stake.value.replace(",", "."))
            comm = float(in_comm.value.replace(",", ".")) / 100
            
            c_score = f"{in_casa.value}-{in_ospite.value}"
            
            if dd_camp.value in df_bibbia.index:
                lim_p = df_bibbia.loc[dd_camp.value, f"PUNTA_{c_score}"]
                lim_b = df_bibbia.loc[dd_camp.value, f"BANCA_{c_score}"]
                
                # Logica Segnale
                ok_p = v_p < lim_p
                ok_b = v_b > lim_b
                trade_on = ok_p and ok_b
                
                # Calcoli Economici
                rischio_fisso = bank * (stake_perc / 100)
                
                # Opzione PUNTA
                prof_p = (rischio_fisso * (v_p - 1)) * (1 - comm)
                
                # Opzione BANCA (Stake calcolato sulla responsabilità)
                puntata_lay = rischio_fisso / (v_b - 1)
                prof_b = puntata_lay * (1 - comm)

                # --- COSTRUZIONE UI RISULTATI ---
                
                # 1. Indicatori Filtri
                col_res.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Row([ft.Icon(ft.Icons.CIRCLE, color="green" if ok_p else "red", size=12), ft.Text(f"Punta < {lim_p}", size=12)]),
                                ft.Row([ft.Icon(ft.Icons.CIRCLE, color="green" if ok_b else "red", size=12), ft.Text(f"Banca > {lim_b}", size=12)]),
                            ], expand=True),
                            ft.Column([
                                ft.Text(f"TARGET: OVER {int(in_casa.value)+int(in_ospite.value)+0.5}", weight="bold", color="#64ffda")
                            ], horizontal_alignment="end")
                        ]),
                        padding=10, bgcolor="#1a1a2e", border_radius=8
                    )
                )

                # 2. Verdetto Centrale
                if trade_on:
                    # Determino il migliore
                    if prof_p >= prof_b:
                        consiglio = "PUNTARE (BACK)"
                        colore_v = "#00c853"
                        dettaglio_stake = f"Punta: € {rischio_fisso:.2f}"
                        netto_v = prof_p
                    else:
                        consiglio = "BANCARE (LAY)"
                        colore_v = "#00c853"
                        dettaglio_stake = f"Stake Lay: € {puntata_lay:.2f}\n(Rischio: € {rischio_fisso:.2f})"
                        netto_v = prof_b

                    col_res.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Text("✅ TRADE ON", size=20, weight="black", color=colore_v),
                                ft.Text(consiglio, size=16, weight="bold"),
                                ft.Divider(color="white24"),
                                ft.Text(dettaglio_stake, textAlign="center"),
                                ft.Text(f"PROFITTO NETTO: € {netto_v:.2f}", size=18, weight="bold", color=colore_v)
                            ], horizontal_alignment="center", spacing=5),
                            padding=20, bgcolor="#16213e", border_radius=12, border=ft.border.all(2, colore_v)
                        )
                    )
                else:
                    col_res.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.Icons.GPP_BAD, color="#ff5252", size=40),
                                ft.Text("RISK OFF", size=22, weight="black", color="#ff5252"),
                                ft.Text("Parametri non soddisfatti", size=14, italic=True)
                            ], horizontal_alignment="center"),
                            padding=20, bgcolor="#16213e", border_radius=12, width=1000
                        )
                    )

            page.update()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Errore: {ex}"))
            page.snack_bar.open = True
            page.update()

    btn = ft.ElevatedButton(
        content=ft.Row([ft.Icon(ft.Icons.SEARCH), ft.Text("ANALIZZA MATCH", weight="bold")], alignment="center"),
        on_click=analizza_click, height=55, style=ft.ButtonStyle(bgcolor="#448aff", color="white", shape=ft.RoundedRectangleBorder(radius=10))
    )

    # LAYOUT MOBILE
    page.add(
        ft.Column([
            # Header
            ft.Row([
                ft.Icon(ft.Icons.ANALYTICS, color="#64ffda", size=30),
                ft.Column([
                    ft.Text("TYPO HT-PRO", size=22, weight="black", letter_spacing=1),
                    ft.Text("MATRIX SCANNER MOBILE", size=10, color="#64ffda", weight="bold"),
                ], spacing=0)
            ], alignment="center"),
            
            ft.Divider(height=10, color="white10"),
            
            # Input Campionato
            dd_camp,
            
            # Input Gol
            ft.Text("RISULTATO ATTUALE", size=11, weight="bold", color="#888888"),
            ft.Row([in_casa, in_ospite], spacing=10),
            
            # Input Quote
            ft.Text("QUOTE LIVE (EXCHANGE)", size=11, weight="bold", color="#888888"),
            ft.Row([in_punta, in_banca], spacing=10),
            
            # Money Management
            ft.Text("MONEY MANAGEMENT", size=11, weight="bold", color="#888888"),
            ft.Row([in_bank, in_stake, in_comm], spacing=5),
            
            ft.Container(btn, padding=ft.padding.only(top=10, bottom=10)),
            
            # Area Risultati
            col_res
        ], spacing=15)
    )

if __name__ == "__main__":
    ft.app(target=main)
