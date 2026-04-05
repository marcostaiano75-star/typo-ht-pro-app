import flet as ft
import pandas as pd
import os

# --- FUNZIONE CARICAMENTO DATI ---
def load_data(filepath):
    # Questo assicura che trovi il file nella stessa cartella dello script
    base_path = os.path.dirname(__file__)
    full_path = os.path.join(base_path, filepath)
    try:
        df = pd.read_csv(filepath, sep=';', header=None, skiprows=2, encoding='utf-8-sig')
        df.set_index(0, inplace=True)
        res_list = ['0-0', '1-0', '0-1', '1-1', '2-0', '0-2', '3-0', '0-3', '2-1', '1-2', '3-1', '1-3', '2-2']
        df.columns = [f"PUNTA_{r}" for r in res_list] + [f"BANCA_{r}" for r in res_list]
        for col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
        return df
    except:
        return None

def main(page: ft.Page):
    # --- CONFIGURAZIONE PAGINA (OTTIMIZZATA) ---
    page.title = "TYPO HT-PRO | Matrix Scanner"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0a0e14" 
    page.window.width, page.window.height = 900, 900 # Dimensione ideale per monitor standard
    page.padding = 20
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.spacing = 10

    df_bibbia = load_data('database_bibbia.csv')

    # --- COSTANTI STILE ---
    color_cyan = "#64ffda"
    color_accent = "#007bff"
    color_error = "#ff5252"
    color_success = "#00c853"
    color_card = "#16213e"

    def analizza_click(e):
        col_res.controls.clear()
        
        if not all([dd_camp.value, in_casa.value, in_ospite.value, in_punta.value, in_banca.value]):
            page.snack_bar = ft.SnackBar(ft.Text("Mancano dati obbligatori!"))
            page.snack_bar.open = True
            page.update()
            return

        try:
            v_p = float(in_punta.value.replace(",", "."))
            v_b = float(in_banca.value.replace(",", "."))
            c_score = f"{in_casa.value}-{in_ospite.value}"
            c_p, c_b = f"PUNTA_{c_score}", f"BANCA_{c_score}"
            
            bank = float(in_bank.value.replace(",", "."))
            stake_perc = float(in_stake_perc.value.replace(",", "."))
            comm = float(in_comm.value.replace(",", ".")) / 100
        except:
            page.snack_bar = ft.SnackBar(ft.Text("Errore: Formato numeri non valido!"))
            page.snack_bar.open = True
            page.update()
            return

        if dd_camp.value in df_bibbia.index and c_p in df_bibbia.columns:
            lim_p = df_bibbia.loc[dd_camp.value, c_p]
            lim_b = df_bibbia.loc[dd_camp.value, c_b]

            # --- LOGICA BINARIA ---
            ok_punta = v_p < lim_p
            ok_banca = v_b > lim_b
            trade_on = ok_punta and ok_banca
            
            mercato = f"OVER {int(in_casa.value) + int(in_ospite.value) + 0.5}"
            
            # --- CALCOLO PROFITTI REALI ---
            rischio_max = bank * (stake_perc / 100)
            
            prof_punta = (rischio_max * (v_p - 1)) * (1 - comm)
            puntata_lay = rischio_max / (v_b - 1)
            prof_banca = puntata_lay * (1 - comm)

            # --- UI: CARD STATUS (PIÙ COMPATTA) ---
            res_card = ft.Container(
                content=ft.Row([
                    ft.Text(f"TARGET: {mercato}", size=16, weight="bold", color=color_cyan),
                    ft.Row([
                        ft.Icon(ft.Icons.VERIFIED if ok_punta else ft.Icons.CANCEL, color="green" if ok_punta else "red", size=18),
                        ft.Text("PUNTA OK" if ok_punta else "PUNTA NO", size=13)
                    ]),
                    ft.Row([
                        ft.Icon(ft.Icons.VERIFIED if ok_banca else ft.Icons.CANCEL, color="green" if ok_banca else "red", size=18),
                        ft.Text("BANCA OK" if ok_banca else "BANCA NO", size=13)
                    ]),
                ], alignment="center", spacing=40),
                padding=12, bgcolor=color_card, border_radius=10, border=ft.border.all(1, "#2e3b4e")
            )

            # --- UI: CARD VERDETTO (CONSIGLIO REALE) ---
            if trade_on:
                if prof_punta >= prof_banca:
                    consiglio = "PUNTARE"
                    profitto_migliore = prof_punta
                else:
                    consiglio = "BANCARE"
                    profitto_migliore = prof_banca
                
                titolo_v = f"✅ TRADE ON - {consiglio} (QUOTA PIÙ FAVOREVOLE)"
                colore_v = color_success
            else:
                consiglio = "ATTENDERE"
                titolo_v = "❌ RISK OFF - NO TRADE"
                colore_v = color_error

            advice_card = ft.Container(
                content=ft.Column([
                    ft.Text(titolo_v, weight="black", size=24, color=colore_v),
                    ft.Text(f"Analisi basata sul massimo profitto netto a rischio fisso (€ {rischio_max:.2f})", size=11, italic=True),
                ], horizontal_alignment="center", spacing=2),
                padding=15, bgcolor="#1a1a2e", border_radius=10, border=ft.border.all(2, colore_v), alignment=ft.alignment.center
            )

            # --- UI: DETTAGLI ECONOMICI (DOPPIA COLONNA) ---
            econ_card = ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text("OPZIONE PUNTA (BACK)", size=11, color=color_accent, weight="bold"),
                        ft.Text(f"Stake: € {rischio_max:.2f}", size=18, weight="bold"),
                        ft.Text(f"Netto: € {prof_punta:.2f}", size=16, color="green", weight="bold"),
                    ], expand=1, spacing=2),
                    ft.VerticalDivider(color="#2e3b4e"),
                    ft.Column([
                        ft.Text("OPZIONE BANCA (LAY)", size=11, color=color_error, weight="bold"),
                        ft.Text(f"Puntata: € {puntata_lay:.2f}", size=18, weight="bold"),
                        ft.Text(f"Netto: € {prof_banca:.2f}", size=16, color="green", weight="bold"),
                    ], expand=1, spacing=2),
                ]),
                padding=15, bgcolor="#0f172a", border_radius=10
            )

            col_res.controls.extend([res_card, advice_card, econ_card])
        else:
            col_res.controls.append(ft.Text("⚠️ Campionato o Risultato non trovato.", color="orange"))
        
        page.update()

    # --- UI LAYOUT COMPATTO ---
    header = ft.Row([
        ft.Column([
            ft.Text("TYPO HT-PRO", size=28, weight="black", color="white"),
            ft.Text("MATRIX SCANNER PROTOCOL", color=color_cyan, size=11, weight="bold"),
        ]),
        ft.Icon(ft.Icons.ANALYTICS, color=color_cyan, size=35)
    ], alignment="spaceBetween")

    lista_camps = sorted(df_bibbia.index.tolist()) if df_bibbia is not None else []
    
    # Riga 1: Match e Risultato
    row_match = ft.Row([
        ft.Column([ft.Text("CAMPIONATO", size=11, weight="bold"), ft.Dropdown(label="Seleziona", width=300, options=[ft.dropdown.Option(c) for c in lista_camps], height=45, text_size=14)], expand=2),
        ft.Column([ft.Text("GOL CASA", size=11, weight="bold"), ft.TextField(value="0", width=100, height=45, text_align="center")], expand=1),
        ft.Column([ft.Text("GOL OSPITE", size=11, weight="bold"), ft.TextField(value="0", width=100, height=45, text_align="center")], expand=1),
    ])
    
    # Riga 2: Quote e Money Management
    row_money = ft.Row([
        ft.Column([ft.Text("QUOTA PUNTA", size=11, weight="bold", color="blue"), ft.TextField(label="Punta", width=130, height=45, color="blue", text_style=ft.TextStyle(weight="bold"))]),
        ft.Column([ft.Text("QUOTA BANCA", size=11, weight="bold", color="red"), ft.TextField(label="Banca", width=130, height=45, color="red", text_style=ft.TextStyle(weight="bold"))]),
        ft.VerticalDivider(),
        ft.Column([ft.Text("BANCA €", size=11, weight="bold"), ft.TextField(value="100", width=100, height=45)]),
        ft.Column([ft.Text("STAKE %", size=11, weight="bold"), ft.TextField(value="5", width=80, height=45)]),
        ft.Column([ft.Text("COMM %", size=11, weight="bold"), ft.TextField(value="4.5", width=80, height=45)]),
    ], alignment="start")

    # Referenziazione per la funzione analizza
    dd_camp = row_match.controls[0].controls[1]
    in_casa = row_match.controls[1].controls[1]
    in_ospite = row_match.controls[2].controls[1]
    in_punta = row_money.controls[0].controls[1]
    in_banca = row_money.controls[1].controls[1]
    in_bank = row_money.controls[3].controls[1]
    in_stake_perc = row_money.controls[4].controls[1]
    in_comm = row_money.controls[5].controls[1]

    btn = ft.ElevatedButton(
        content=ft.Row([ft.Icon(ft.Icons.RADAR), ft.Text("ANALIZZA MATCH", weight="bold")], alignment="center"),
        style=ft.ButtonStyle(color="white", bgcolor=color_accent, shape=ft.RoundedRectangleBorder(radius=8)),
        width=400, height=50, on_click=analizza_click
    )

    col_res = ft.Column(spacing=8)

    page.add(
        header,
        ft.Divider(height=10, color="#2e3b4e"),
        ft.Container(ft.Column([row_match, row_money], spacing=15), padding=10),
        ft.Row([btn], alignment="center"),
        ft.Divider(height=10, color="#2e3b4e"),
        col_res
    )

if __name__ == "__main__":
    ft.app(target=main)