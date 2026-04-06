import flet as ft
import pandas as pd
import os
import sys

def load_data(filename):
    # Cerca il file in diversi percorsi per compatibilità Windows/Android
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    
    paths_to_try = [
        os.path.join(base_path, "assets", filename), # Percorso APK
        os.path.join(base_path, filename),           # Percorso locale
        filename                                     # Fallback
    ]
    
    for full_path in paths_to_try:
        if os.path.exists(full_path):
            try:
                # Caricamento specifico per la struttura della "Bibbia"
                df = pd.read_csv(full_path, sep=';', header=None, skiprows=2, encoding='utf-8-sig')
                df.set_index(0, inplace=True)
                res_list = ['0-0', '1-0', '0-1', '1-1', '2-0', '0-2', '3-0', '0-3', '2-1', '1-2', '3-1', '1-3', '2-2']
                df.columns = [f"PUNTA_{r}" for r in res_list] + [f"BANCA_{r}" for r in res_list]
                
                # Pulizia virgole e conversione numerica
                for col in df.columns:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
                return df
            except Exception as e:
                print(f"Errore caricamento: {e}")
                continue
    return None

def main(page: ft.Page):
    # Configurazione Mobile
    page.title = "TYPO HT-PRO MOBILE"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0a0e14"
    page.scroll = ft.ScrollMode.AUTO 
    page.padding = 15
    page.assets_dir = "assets" # Specifica la cartella assets

    # Carica il database
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
    in_stake_perc = ft.TextField(label="STAKE %", value="5", expand=1, keyboard_type="number")
    in_comm = ft.TextField(label="COMM %", value="4.5", expand=1, keyboard_type="number")

    col_res = ft.Column(spacing=10)

    def analizza_click(e):
        col_res.controls.clear()
        
        # Validazione campi
        if not dd_camp.value or not in_punta.value or not in_banca.value:
            page.snack_bar = ft.SnackBar(ft.Text("Mancano dati obbligatori!"))
            page.snack_bar.open = True
            page.update()
            return

        try:
            # Conversione valori
            v_p = float(in_punta.value.replace(",", "."))
            v_b = float(in_banca.value.replace(",", "."))
            bank = float(in_bank.value.replace(",", "."))
            stake_perc = float(in_stake_perc.value.replace(",", "."))
            comm = float(in_comm.value.replace(",", ".")) / 100
            
            c_score = f"{in_casa.value}-{in_ospite.value}"
            
            if dd_camp.value in df_bibbia.index:
                # Estrazione limiti dal database
                try:
                    lim_p = df_bibbia.loc[dd_camp.value, f"PUNTA_{c_score}"]
                    lim_b = df_bibbia.loc[dd_camp.value, f"BANCA_{c_score}"]
                except:
                    col_res.controls.append(ft.Text("⚠️ Risultato non supportato dal DB", color="orange"))
                    page.update()
                    return

                # LOGICA FILTRI (Entrambi devono essere OK)
                ok_p = v_p < lim_p
                ok_b = v_b > lim_b
                trade_on = ok_p and ok_b
                
                # CALCOLO ECONOMICO (Basato su Rischio Fisso)
                rischio_max = bank * (stake_perc / 100)
                
                # Opzione PUNTA
                prof_punta = (rischio_max * (v_p - 1)) * (1 - comm)
                
                # Opzione BANCA (Calcolo stake lay per avere responsabilità = rischio_max)
                puntata_lay = rischio_max / (v_b - 1)
                prof_banca = puntata_lay * (1 - comm)

                # --- DISEGNO RISULTATI ---
                
                # Indicatori limiti
                col_res.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE if ok_p else ft.Icons.CANCEL, color="green" if ok_p else "red", size=16), ft.Text(f"Punta < {lim_p}", size=13)]),
                                ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE if ok_b else ft.Icons.CANCEL, color="green" if ok_b else "red", size=16), ft.Text(f"Banca > {lim_b}", size=13)]),
                            ], expand=True),
                            ft.Text(f"TARGET: OVER {int(in_casa.value)+int(in_ospite.value)+0.5}", weight="bold", color="#64ffda", size=14)
                        ]),
                        padding=12, bgcolor="#1a1a2e", border_radius=8
                    )
                )

                if trade_on:
                    # Determinazione opzione migliore
                    if prof_punta >= prof_banca:
                        consiglio = "PUNTARE (BACK)"
                        testo_stake = f"Punta esattamente: € {rischio_max:.2f}"
                        netto = prof_punta
                    else:
                        consiglio = "BANCARE (LAY)"
                        testo_stake = f"Puntata da scrivere: € {puntata_lay:.2f}\n(Responsabilità: € {rischio_max:.2f})"
                        netto = prof_banca

                    col_res.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Text("✅ TRADE ON", size=22, weight="black", color="#00c853"),
                                ft.Text(consiglio, size=18, weight="bold", color="white"),
                                ft.Divider(color="white24"),
                                ft.Text(testo_stake, textAlign="center", size=15),
                                ft.Text(f"PROFITTO NETTO: € {netto:.2f}", size=20, weight="bold", color="#00c853")
                            ], horizontal_alignment="center", spacing=8),
                            padding=20, bgcolor="#16213e", border_radius=12, border=ft.border.all(2, "#00c853")
                        )
                    )
                else:
                    # Segnale RISK OFF
                    col_res.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.Icons.GPP_BAD, color="#ff5252", size=40),
                                ft.Text("❌ RISK OFF", size=22, weight="black", color="#ff5252"),
                                ft.Text("Parametri non soddisfatti", size=14, italic=True)
                            ], horizontal_alignment="center"),
                            padding=25, bgcolor="#16213e", border_radius=12, width=1000
                        )
                    )
            else:
                col_res.controls.append(ft.Text("⚠️ Campionato non trovato nel database.", color="orange"))
                
            page.update()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Errore: {ex}"))
            page.snack_bar.open = True
            page.update()

    # Bottone Analizza
    btn = ft.ElevatedButton(
        content=ft.Row([ft.Icon(ft.Icons.RADAR), ft.Text("ANALIZZA MATCH", weight="bold")], alignment="center"),
        on_click=analizza_click, height=55, style=ft.ButtonStyle(bgcolor="#007bff", color="white", shape=ft.RoundedRectangleBorder(radius=10))
    )

    # LAYOUT PAGINA
    page.add(
        ft.Column([
            # Titolo
            ft.Row([
                ft.Icon(ft.Icons.ANALYTICS, color="#64ffda", size=32),
                ft.Column([
                    ft.Text("TYPO HT-PRO", size=24, weight="black", letter_spacing=1),
                    ft.Text("MATRIX SCANNER MOBILE", size=10, color="#64ffda", weight="bold"),
                ], spacing=0)
            ], alignment="center"),
            
            ft.Divider(height=10, color="white10"),
            
            # Form
            dd_camp,
            
            ft.Text("GOL ATTUALI", size=11, weight="bold", color="#888888"),
            ft.Row([in_casa, in_ospite], spacing=10),
            
            ft.Text("QUOTE EXCHANGE LIVE", size=11, weight="bold", color="#888888"),
            ft.Row([in_punta, in_banca], spacing=10),
            
            ft.Text("GESTIONE STAKE", size=11, weight="bold", color="#888888"),
            ft.Row([in_bank, in_stake_perc, in_comm], spacing=5),
            
            ft.Container(btn, padding=ft.padding.only(top=10, bottom=10)),
            
            # Risultato
            col_res
        ], spacing=15)
    )

if __name__ == "__main__":
    ft.app(target=main)
