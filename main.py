import flet as ft
import pandas as pd
import os

def load_data(filename):
    # Cerca il file semplicemente nella cartella dove gira lo script
    # Questo è il modo più sicuro che ha funzionato ieri
    try:
        if os.path.exists(filename):
            df = pd.read_csv(filename, sep=';', header=None, skiprows=2, encoding='utf-8-sig')
            df.set_index(0, inplace=True)
            res_list = ['0-0', '1-0', '0-1', '1-1', '2-0', '0-2', '3-0', '0-3', '2-1', '1-2', '3-1', '1-3', '2-2']
            df.columns = [f"PUNTA_{r}" for r in res_list] + [f"BANCA_{r}" for r in res_list]
            for col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
            return df
    except Exception as e:
        print(f"Errore: {e}")
    return None

def main(page: ft.Page):
    page.title = "TYPO HT-PRO MOBILE"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0a0e14"
    page.scroll = ft.ScrollMode.AUTO 
    page.padding = 15

    # Carica i dati
    df_bibbia = load_data('database_bibbia.csv')

    # --- ELEMENTI UI ---
    dd_camp = ft.Dropdown(
        label="CAMPIONATO",
        options=[ft.dropdown.Option(c) for c in sorted(df_bibbia.index.tolist())] if df_bibbia is not None else [ft.dropdown.Option("DB NON CARICATO")],
        text_size=14, height=60, border_color="#448aff"
    )

    in_casa = ft.TextField(label="GOL CASA", value="0", expand=1, keyboard_type="number", text_align="center")
    in_ospite = ft.TextField(label="GOL OSPITE", value="0", expand=1, keyboard_type="number", text_align="center")
    in_punta = ft.TextField(label="QUOTA PUNTA", expand=1, keyboard_type="number", color="#448aff")
    in_banca = ft.TextField(label="QUOTA BANCA", expand=1, keyboard_type="number", color="#ff5252")
    in_bank = ft.TextField(label="BANK €", value="100", expand=1, keyboard_type="number")
    in_stake = ft.TextField(label="STAKE %", value="5", expand=1, keyboard_type="number")
    in_comm = ft.TextField(label="COMM %", value="4.5", expand=1, keyboard_type="number")

    col_res = ft.Column(spacing=10)

    def analizza_click(e):
        col_res.controls.clear()
        if df_bibbia is None:
            page.snack_bar = ft.SnackBar(ft.Text("Errore: Database non trovato!"))
            page.snack_bar.open = True
            page.update()
            return

        if not dd_camp.value or not in_punta.value or not in_banca.value:
            page.snack_bar = ft.SnackBar(ft.Text("Inserisci tutti i dati!"))
            page.snack_bar.open = True
            page.update()
            return

        try:
            v_p = float(in_punta.value.replace(",", "."))
            v_b = float(in_banca.value.replace(",", "."))
            bank = float(in_bank.value.replace(",", "."))
            s_p = float(in_stake.value.replace(",", "."))
            comm = float(in_comm.value.replace(",", ".")) / 100
            c_score = f"{in_casa.value}-{in_ospite.value}"
            
            lim_p = df_bibbia.loc[dd_camp.value, f"PUNTA_{c_score}"]
            lim_b = df_bibbia.loc[dd_camp.value, f"BANCA_{c_score}"]
            
            ok_p, ok_b = v_p < lim_p, v_b > lim_b
            trade_on = ok_p and ok_b
            
            rischio = bank * (s_p / 100)
            prof_p = (rischio * (v_p - 1)) * (1 - comm)
            lay_stake = rischio / (v_b - 1)
            prof_b = lay_stake * (1 - comm)

            # Indicatori filtri
            col_res.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Row([ft.Icon(ft.Icons.CIRCLE, color="green" if ok_p else "red", size=12), ft.Text(f"Punta < {lim_p}")]),
                            ft.Row([ft.Icon(ft.Icons.CIRCLE, color="green" if ok_b else "red", size=12), ft.Text(f"Banca > {lim_b}")]),
                        ]),
                        ft.Text(f"TARGET: OVER {int(in_casa.value)+int(in_ospite.value)+0.5}", weight="bold", color="#64ffda")
                    ], alignment="spaceBetween"),
                    padding=10, bgcolor="#1a1a2e", border_radius=8
                )
            )

            if trade_on:
                scelta = "PUNTARE" if prof_p >= prof_b else "BANCARE"
                p_netto = prof_p if prof_p >= prof_b else prof_b
                dettaglio = f"Stake: € {rischio:.2f}" if scelta == "PUNTARE" else f"Puntata Lay: € {lay_stake:.2f}\n(Rischio: € {rischio:.2f})"
                
                col_res.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text("✅ TRADE ON", size=20, weight="black", color="#00c853"),
                            ft.Text(scelta, size=18, weight="bold"),
                            ft.Text(dettaglio, textAlign="center"),
                            ft.Text(f"NETTO: € {p_netto:.2f}", size=20, weight="bold", color="#00c853")
                        ], horizontal_alignment="center"),
                        padding=20, bgcolor="#16213e", border_radius=12, border=ft.border.all(2, "#00c853")
                    )
                )
            else:
                col_res.controls.append(
                    ft.Container(
                        content=ft.Text("❌ RISK OFF", size=20, weight="black", color="#ff5252"),
                        padding=20, bgcolor="#16213e", border_radius=12, alignment=ft.alignment.center
                    )
                )
            page.update()
        except: pass

    btn = ft.ElevatedButton(
        content=ft.Row([ft.Icon(ft.Icons.SEARCH), ft.Text("ANALIZZA MATCH", weight="bold")], alignment="center"),
        on_click=analizza_click, height=50, style=ft.ButtonStyle(bgcolor="#007bff", color="white")
    )

    page.add(
        ft.Column([
            ft.Row([ft.Icon(ft.Icons.ANALYTICS, color="#64ffda"), ft.Text("TYPO HT-PRO MOBILE", size=20, weight="black")], alignment="center"),
            ft.Divider(height=10),
            dd_camp,
            ft.Row([in_casa, in_ospite], spacing=10),
            ft.Row([in_punta, in_banca], spacing=10),
            ft.Row([in_bank, in_stake, in_comm], spacing=5),
            ft.Container(btn, padding=10),
            col_res
        ])
    )

if __name__ == "__main__":
    ft.app(target=main)
