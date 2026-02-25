"""
IMCE Dashboard — Contractors Page (Deep Analysis)
Filters: Site → Company
Sections: KPIs, E&S Instruments, Workforce, Incidents, PPE,
          Compliance, Training, Waste & GRM, Scoring Table
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

# ─────────────────────────────────────────────────────────────────────────────
# DESIGN TOKENS
# ─────────────────────────────────────────────────────────────────────────────

C = {
    'primary':   '#0D2137',
    'secondary': '#00BFA5',
    'accent':    '#1565C0',
    'success':   '#2E7D32',
    'warning':   '#E65100',
    'danger':    '#B71C1C',
    'light_bg':  '#F0F4F8',
    'card':      '#FFFFFF',
    'muted':     '#607D8B',
    'border':    '#E0E8F0',
    'p1': '#1565C0', 'p2': '#00BFA5', 'p3': '#FFA726',
    'p4': '#EF5350', 'p5': '#AB47BC', 'p6': '#26A69A',
}

PALETTE = [C['p1'], C['p2'], C['p3'], C['p4'], C['p5'], C['p6']]

BASE_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Nunito, sans-serif', color=C['primary'], size=13),
    margin=dict(l=10, r=10, t=35, b=10),
    legend=dict(
        bgcolor='rgba(255,255,255,0.9)',
        bordercolor=C['border'], borderwidth=1,
        font=dict(size=12),
    ),
    hoverlabel=dict(
        bgcolor=C['primary'], bordercolor=C['border'],
        font=dict(family='Nunito, sans-serif', size=13, color='#FFFFFF'),
    ),
    xaxis=dict(gridcolor=C['border'], linecolor=C['border'], tickfont=dict(size=12)),
    yaxis=dict(gridcolor=C['border'], linecolor=C['border'], tickfont=dict(size=12)),
)

# ─────────────────────────────────────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────────────────────────────────────

COMPANY_MAP = {
    'NPD LTD / Jv prominent Engineering solutions and United Contractors LTD': 'NPD LTD (JV)',
    'CRB/ PROMINENT ENG SOLUTION AND UNITED CONTRACTORS': 'CRBC (JV)',
    'CRBC china road and bridge corporation/Net consult PLC': 'CRBC/NET',
    'CRBC /NET CONSULTANT PLC': 'CRBC/NET',
    'CRBC / NET consultant PLC': 'CRBC/NET',
    'NPD/ UNITER CONTRACTORS': 'NPD (JV)',
}

INST_COLS = ['inst_esia_esmp', 'inst_cesmp', 'inst_waste_plan',
             'inst_ohs_plan', 'inst_borrow_pit_permit']
INST_LABELS = ['ESIA/ESMP', 'C-ESMP', 'Waste Plan', 'OHS Plan', 'Borrow Pit Permit']

COMP_BOOL_COLS = ['grm_logbook', 'chance_finds_procedure',
                  'waste_disposal_auth', 'es_in_bidding']
COMP_LABELS    = ['GRM Logbook', 'Chance Finds Procedure',
                  'Waste Auth.', 'E&S in Bidding']


def load_contractors():
    import os
    paths = [
        'contractors_clean.csv',
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'contractors_clean.csv'),
    ]
    df = pd.DataFrame()
    for p in paths:
        if os.path.exists(p):
            df = pd.read_csv(p)
            break
    if df.empty:
        return df

    df['site_name']     = df['site_name'].str.strip()
    df['company_clean'] = df['company_name'].replace(COMPANY_MAP).str.strip()

    # Instrument score (0-100)
    df['inst_score'] = df[INST_COLS].sum(axis=1) / len(INST_COLS) * 100

    # Compliance score (grm_logbook, chance_finds, waste_auth, es_in_bidding)
    for c in COMP_BOOL_COLS:
        df[c + '_bool'] = df[c].eq('Yes').astype(int)
    df['comp_score'] = (
        df[[c + '_bool' for c in COMP_BOOL_COLS]].sum(axis=1) / len(COMP_BOOL_COLS) * 100
    )

    # Training coverage %
    df['training_coverage'] = (
        df['training_exact_number'] / df['total_workers'] * 100
    ).fillna(0).clip(upper=100)

    # Global E&S score
    df['global_score'] = (
        df['inst_score'] * 0.3 +
        df['comp_score'] * 0.3 +
        df['training_coverage'].clip(upper=100) * 0.2 +
        df['women_percent'].clip(upper=50) / 50 * 100 * 0.1 +
        df['local_percent'].clip(upper=100) * 0.1
    )

    return df


CONTRACTORS = load_contractors()


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def card(children, style=None):
    base = {
        'background': C['card'], 'borderRadius': '12px',
        'padding': '20px 24px',
        'boxShadow': '0 2px 8px rgba(13,33,55,0.07)', 'height': '100%',
    }
    if style:
        base.update(style)
    return html.Div(children, style=base)


def section_title(title, subtitle=None):
    return html.Div([
        html.H5(title, style={
            'margin': '0 0 2px 0', 'fontWeight': '700',
            'fontSize': '15px', 'color': C['primary'],
        }),
        html.P(subtitle, style={'margin': '0', 'fontSize': '12px', 'color': C['muted']})
        if subtitle else html.Span(),
    ], style={
        'marginBottom': '14px', 'paddingBottom': '10px',
        'borderBottom': f'2px solid {C["border"]}',
    })


def kpi(title, value, sub=None, color=C['accent']):
    return html.Div([
        html.P(title, style={
            'margin': '0 0 6px 0', 'fontSize': '11px', 'fontWeight': '700',
            'textTransform': 'uppercase', 'letterSpacing': '1.2px', 'color': C['muted'],
        }),
        html.H2(value, style={
            'margin': '0 0 4px 0', 'fontSize': '30px',
            'fontWeight': '900', 'color': color, 'lineHeight': '1',
        }),
        html.P(sub or '', style={'margin': '0', 'fontSize': '12px', 'color': C['muted']}),
    ], style={
        'background': C['card'], 'borderRadius': '12px', 'padding': '18px 20px',
        'boxShadow': '0 2px 8px rgba(13,33,55,0.07)',
        'borderTop': f'4px solid {color}', 'height': '100%',
    })


def get_df(site, company):
    df = CONTRACTORS.copy()
    if df.empty:
        return df
    if site and site != 'ALL':
        df = df[df['site_name'] == site]
    if company and company != 'ALL':
        df = df[df['company_clean'] == company]
    return df


def score_color(pct):
    if pct >= 75:
        return C['success'], '#E8F5E9'
    elif pct >= 50:
        return C['warning'], '#FFF3E0'
    return C['danger'], '#FFEBEE'


def prog_bar(pct, color, width='80px'):
    return html.Div([
        html.Div([
            html.Div(style={
                'width': f'{min(float(pct), 100):.0f}%',
                'height': '6px', 'background': color, 'borderRadius': '3px',
            }),
        ], style={
            'background': C['border'], 'borderRadius': '3px',
            'overflow': 'hidden', 'width': width,
            'display': 'inline-block', 'verticalAlign': 'middle',
            'marginRight': '6px',
        }),
        html.Span(f'{float(pct):.0f}%', style={
            'fontSize': '12px', 'fontWeight': '700',
            'color': color, 'verticalAlign': 'middle',
        }),
    ])


# ─────────────────────────────────────────────────────────────────────────────
# FILTER BAR
# ─────────────────────────────────────────────────────────────────────────────

def filter_bar():
    sites = sorted(CONTRACTORS['site_name'].unique().tolist()) if not CONTRACTORS.empty else []
    dd = {'width': '240px', 'fontFamily': 'Nunito, sans-serif', 'fontSize': '13px'}
    lb = {
        'fontSize': '11px', 'fontWeight': '700', 'textTransform': 'uppercase',
        'letterSpacing': '1px', 'color': C['muted'], 'marginBottom': '4px',
        'display': 'block',
    }
    return html.Div([
        html.Div([
            html.Label('Site', style=lb),
            dcc.Dropdown(
                id='contr-site-filter',
                options=[{'label': 'All Sites', 'value': 'ALL'}] +
                        [{'label': s, 'value': s} for s in sites],
                value='ALL', clearable=False, style=dd,
            ),
        ]),
        html.Div([
            html.Label('Company', style=lb),
            dcc.Dropdown(
                id='contr-company-filter',
                options=[{'label': 'All Companies', 'value': 'ALL'}],
                value='ALL', clearable=False, style=dd,
            ),
        ]),
    ], style={
        'display': 'flex', 'alignItems': 'flex-end', 'gap': '20px',
        'background': C['card'], 'padding': '16px 24px', 'borderRadius': '10px',
        'boxShadow': '0 2px 8px rgba(13,33,55,0.05)',
        'marginBottom': '24px', 'width': 'fit-content',
    })


# ─────────────────────────────────────────────────────────────────────────────
# LAYOUT
# ─────────────────────────────────────────────────────────────────────────────

def layout():
    if CONTRACTORS.empty:
        return html.Div('contractors_clean.csv not found.',
                        style={'padding': '40px 40px 40px 260px'})

    n            = len(CONTRACTORS)
    incidents    = CONTRACTORS['incidents_occurred'].eq('Yes').sum()
    total_w      = CONTRACTORS['total_workers'].sum()
    avg_women    = CONTRACTORS['women_percent'].mean()
    avg_local    = CONTRACTORS['local_percent'].mean()

    if avg_women >= 30 and incidents / n <= 0.5:
        sc, st, sb = C['success'], '● ON TRACK', '#E8F5E9'
    elif avg_women >= 20 or incidents / n <= 0.7:
        sc, st, sb = C['warning'], '● ATTENTION REQUIRED', '#FFF3E0'
    else:
        sc, st, sb = C['danger'], '● CRITICAL', '#FFEBEE'

    return html.Div([

        # PAGE HEADER
        html.Div([
            html.Div([
                html.H2('Contractors', style={
                    'margin': '0 0 4px 0', 'fontWeight': '900',
                    'fontSize': '26px', 'color': C['primary'],
                }),
                html.P(
                    f'{n} contractors interviewed across {CONTRACTORS["site_name"].nunique()} sites — IMCE Project Rwanda',
                    style={'margin': '0', 'color': C['muted'], 'fontSize': '14px'},
                ),
            ]),
            html.Span(st, style={
                'background': sb, 'color': sc, 'padding': '6px 16px',
                'borderRadius': '20px', 'fontSize': '13px', 'fontWeight': '700',
                'border': f'1px solid {sc}',
            }),
        ], style={
            'display': 'flex', 'justifyContent': 'space-between',
            'alignItems': 'center', 'marginBottom': '24px',
        }),

        # FILTERS
        filter_bar(),

        # SECTION 1 — KPIs
        dbc.Row([
            dbc.Col(html.Div(id='c-kpi-total'),     md=2),
            dbc.Col(html.Div(id='c-kpi-workers'),   md=2),
            dbc.Col(html.Div(id='c-kpi-women'),     md=2),
            dbc.Col(html.Div(id='c-kpi-local'),     md=2),
            dbc.Col(html.Div(id='c-kpi-incidents'), md=2),
            dbc.Col(html.Div(id='c-kpi-es'),        md=2),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 2 — E&S Instruments
        dbc.Row([
            dbc.Col([card([
                section_title('E&S Instruments Availability',
                              'How many contractors have each required E&S instrument on site?'),
                dcc.Graph(id='c-instruments',
                          config={'displayModeBar': False}, style={'height': '280px'}),
            ])], md=5),
            dbc.Col([card([
                section_title('E&S Instruments Matrix — Per Site',
                              '✓ = available / ✗ = missing — identify gaps immediately'),
                html.Div(id='c-inst-matrix'),
            ])], md=7),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 3 — Staff specialists
        dbc.Row([
            dbc.Col([card([
                section_title('E&S Staff Specialists',
                              'Do contractors have dedicated environmental, social and OHS specialists?'),
                dcc.Graph(id='c-staff',
                          config={'displayModeBar': False}, style={'height': '240px'}),
            ])], md=4),
            dbc.Col([card([
                section_title('E&S in Bidding Documents',
                              'Which contractors included E&S requirements in their bidding documents?'),
                dcc.Graph(id='c-es-bidding',
                          config={'displayModeBar': False}, style={'height': '240px'}),
            ])], md=4),
            dbc.Col([card([
                section_title('Payment Frequency',
                              'How frequently are workers paid across all sites?'),
                dcc.Graph(id='c-payment',
                          config={'displayModeBar': False}, style={'height': '240px'}),
            ])], md=4),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 4 — Workforce
        dbc.Row([
            dbc.Col([card([
                section_title('Women in Workforce by Site',
                              '% women among current workers — World Bank target: 30%'),
                dcc.Graph(id='c-women-site',
                          config={'displayModeBar': False}, style={'height': '300px'}),
            ])], md=6),
            dbc.Col([card([
                section_title('Local vs Non-Local Workers by Site',
                              'Proportion of locally-recruited workers — key World Bank indicator'),
                dcc.Graph(id='c-local-site',
                          config={'displayModeBar': False}, style={'height': '300px'}),
            ])], md=6),
        ], className='g-3', style={'marginBottom': '24px'}),

        dbc.Row([
            dbc.Col([card([
                section_title('Total vs Current Workers',
                              'How many workers remain active on site vs total mobilized?'),
                dcc.Graph(id='c-workers-total-current',
                          config={'displayModeBar': False}, style={'height': '280px'}),
            ])], md=7),
            dbc.Col([card([
                section_title('Workforce Gender Split',
                              'Men vs women breakdown across all selected sites'),
                dcc.Graph(id='c-gender-split',
                          config={'displayModeBar': False}, style={'height': '280px'}),
            ])], md=5),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 5 — Incidents & Safety
        dbc.Row([
            dbc.Col([card([
                section_title('Incidents by Site',
                              'Number of incidents reported per contractor — documented and verified'),
                dcc.Graph(id='c-incidents',
                          config={'displayModeBar': False}, style={'height': '280px'}),
            ])], md=6),
            dbc.Col([card([
                section_title('PPE Distribution Frequency',
                              'How often do contractors distribute PPE to their workers?'),
                dcc.Graph(id='c-ppe-freq',
                          config={'displayModeBar': False}, style={'height': '280px'}),
            ])], md=3),
            dbc.Col([card([
                section_title('PPE Types Provided',
                              'Which PPE types are available on site across all contractors?'),
                dcc.Graph(id='c-ppe-types',
                          config={'displayModeBar': False}, style={'height': '280px'}),
            ])], md=3),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 6 — Training
        dbc.Row([
            dbc.Col([card([
                section_title('Training Coverage by Site',
                              '% of total workers who received E&S training — most sites are critically low'),
                dcc.Graph(id='c-training-coverage',
                          config={'displayModeBar': False}, style={'height': '300px'}),
            ])], md=7),
            dbc.Col([card([
                section_title('Training Numbers',
                              'Absolute number of workers trained vs total workforce per site'),
                dcc.Graph(id='c-training-numbers',
                          config={'displayModeBar': False}, style={'height': '300px'}),
            ])], md=5),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 7 — Waste & GRM
        dbc.Row([
            dbc.Col([card([
                section_title('Waste Disposal Methods',
                              'How are contractors managing construction waste on their sites?'),
                dcc.Graph(id='c-waste',
                          config={'displayModeBar': False}, style={'height': '260px'}),
            ])], md=4),
            dbc.Col([card([
                section_title('GRM & Compliance Indicators',
                              'GRM logbook, chance finds procedure, waste authorization, E&S in bidding'),
                dcc.Graph(id='c-compliance',
                          config={'displayModeBar': False}, style={'height': '260px'}),
            ])], md=4),
            dbc.Col([card([
                section_title('Compliance Quick View',
                              'Key compliance flags across all contractors'),
                html.Div(id='c-compliance-flags'),
            ])], md=4),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 8 — Contractor scoring table
        dbc.Row([
            dbc.Col([card([
                section_title('Contractor E&S Scoring Dashboard',
                              'Composite score per site: Instruments (30%) + Compliance (30%) + Training (20%) + Gender (10%) + Local (10%)'),
                html.Div(id='c-scoring-table'),
            ])], md=12),
        ], className='g-3'),

    ], style={
        'padding': '32px 32px 48px 252px',
        'minHeight': '100vh',
        'background': C['light_bg'],
    })


# ─────────────────────────────────────────────────────────────────────────────
# CALLBACKS
# ─────────────────────────────────────────────────────────────────────────────

def register_callbacks(app):

    # ── CASCADE: company options ──────────────────────────────────────────────
    @app.callback(
        Output('contr-company-filter', 'options'),
        Output('contr-company-filter', 'value'),
        Input('contr-site-filter', 'value'),
    )
    def update_company_options(site):
        df = CONTRACTORS.copy()
        if site and site != 'ALL':
            df = df[df['site_name'] == site]
        companies = sorted(df['company_clean'].dropna().unique().tolist())
        options = [{'label': 'All Companies', 'value': 'ALL'}] + \
                  [{'label': c, 'value': c} for c in companies]
        return options, 'ALL'

    # ── KPIs ─────────────────────────────────────────────────────────────────
    @app.callback(
        Output('c-kpi-total',     'children'),
        Output('c-kpi-workers',   'children'),
        Output('c-kpi-women',     'children'),
        Output('c-kpi-local',     'children'),
        Output('c-kpi-incidents', 'children'),
        Output('c-kpi-es',        'children'),
        Input('contr-site-filter',    'value'),
        Input('contr-company-filter', 'value'),
    )
    def update_kpis(site, company):
        df = get_df(site, company)
        if df.empty:
            return [html.Div('—')] * 6
        n           = len(df)
        total_w     = int(df['current_workers'].sum())
        avg_women   = float(df['women_percent'].mean())
        avg_local   = float(df['local_percent'].mean())
        inc_count   = int(df['incidents_occurred'].eq('Yes').sum())
        total_inc   = int(df['incidents_count'].fillna(0).sum())
        es_ok       = int(df['es_in_bidding'].eq('Yes').sum())

        wc = C['success'] if avg_women >= 30 else (C['warning'] if avg_women >= 20 else C['danger'])
        lc = C['success'] if avg_local >= 70 else (C['warning'] if avg_local >= 50 else C['danger'])
        ic = C['danger']  if inc_count > n * 0.6 else (C['warning'] if inc_count > n * 0.3 else C['success'])
        ec = C['success'] if es_ok == n else (C['warning'] if es_ok >= n * 0.7 else C['danger'])

        return (
            kpi('Contractors', str(n),
                f'{df["site_name"].nunique()} sites covered', C['accent']),
            kpi('Current Workers', f'{total_w:,}',
                f'Total mobilized: {int(df["total_workers"].sum()):,}', C['p2']),
            kpi('Women in Workforce', f'{avg_women:.0f}%',
                'Average across all sites (target: 30%)', wc),
            kpi('Local Workers', f'{avg_local:.0f}%',
                'Average local recruitment rate', lc),
            kpi('Sites with Incidents', str(inc_count),
                f'{total_inc} total incidents reported', ic),
            kpi('E&S in Bidding', f'{es_ok}/{n}',
                'Contractors with E&S clauses in contract', ec),
        )

    # ── E&S INSTRUMENTS BAR ───────────────────────────────────────────────────
    @app.callback(
        Output('c-instruments', 'figure'),
        Input('contr-site-filter',    'value'),
        Input('contr-company-filter', 'value'),
    )
    def instruments(site, company):
        df = get_df(site, company)
        if df.empty:
            return go.Figure()
        n    = len(df)
        vals = [int(df[col].sum()) for col in INST_COLS]
        pcts = [v / n * 100 for v in vals]
        colors = [C['success'] if p == 100 else (C['warning'] if p >= 80 else C['danger'])
                  for p in pcts]

        fig = go.Figure(go.Bar(
            y=INST_LABELS, x=pcts, orientation='h',
            marker_color=colors, marker_line_width=0,
            text=[f'{v}/{n} ({p:.0f}%)' for v, p in zip(vals, pcts)],
            textposition='outside', textfont=dict(size=12),
        ))
        fig.add_vline(x=100, line_dash='dot', line_color=C['muted'],
                      annotation_text='100% required',
                      annotation_font=dict(size=11, color=C['muted']))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_xaxes(range=[0, 125], ticksuffix='%')
        return fig

    # ── INSTRUMENTS MATRIX ────────────────────────────────────────────────────
    @app.callback(
        Output('c-inst-matrix', 'children'),
        Input('contr-site-filter',    'value'),
        Input('contr-company-filter', 'value'),
    )
    def inst_matrix(site, company):
        df = get_df(site, company)
        if df.empty:
            return html.Div('—')

        headers = ['Site', 'Company'] + INST_LABELS
        rows = []
        for _, r in df.iterrows():
            cells = [
                html.Td(r['site_name'][:28], style={
                    'fontSize': '11px', 'fontWeight': '700',
                    'padding': '7px 10px', 'color': C['primary'],
                    'maxWidth': '160px',
                }),
                html.Td(r['company_clean'][:18], style={
                    'fontSize': '11px', 'color': C['muted'],
                    'padding': '7px 10px',
                }),
            ]
            for col in INST_COLS:
                ok = r[col] == 1
                cells.append(html.Td(
                    html.Span('✓' if ok else '✗', style={
                        'fontSize': '14px', 'fontWeight': '900',
                        'color': C['success'] if ok else C['danger'],
                    }),
                    style={'textAlign': 'center', 'padding': '7px 8px'},
                ))
            rows.append(html.Tr(cells, style={
                'borderBottom': f'1px solid {C["border"]}',
                'background': '#FFEBEE' if any(r[c] == 0 for c in INST_COLS) else 'white',
            }))

        return html.Table([
            html.Thead(html.Tr([
                html.Th(h, style={
                    'padding': '8px 10px', 'fontSize': '10px', 'fontWeight': '700',
                    'textTransform': 'uppercase', 'letterSpacing': '1px',
                    'color': C['muted'], 'background': C['light_bg'],
                    'borderBottom': f'2px solid {C["border"]}',
                    'textAlign': 'center' if i > 1 else 'left',
                }) for i, h in enumerate(headers)
            ])),
            html.Tbody(rows),
        ], style={'width': '100%', 'borderCollapse': 'collapse', 'fontSize': '12px'})

    # ── STAFF ─────────────────────────────────────────────────────────────────
    @app.callback(
        Output('c-staff', 'figure'),
        Input('contr-site-filter',    'value'),
        Input('contr-company-filter', 'value'),
    )
    def staff(site, company):
        df = get_df(site, company)
        if df.empty:
            return go.Figure()
        n = len(df)
        specialists = {
            'Env. Specialist':    int(df['staff_env_specialist'].sum()),
            'Social Specialist':  int(df['staff_social_specialist'].sum()),
            'OHS Specialist':     int(df['staff_ohs_specialist'].sum()),
        }
        pcts   = [v / n * 100 for v in specialists.values()]
        colors = [C['success'] if p == 100 else (C['warning'] if p >= 80 else C['danger'])
                  for p in pcts]

        fig = go.Figure(go.Bar(
            x=list(specialists.keys()), y=pcts,
            marker_color=colors, marker_line_width=0,
            text=[f'{v}/{n}' for v in specialists.values()],
            textposition='outside', textfont=dict(size=13),
        ))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_yaxes(title='% of Contractors', ticksuffix='%', range=[0, 120])
        return fig

    # ── E&S IN BIDDING ────────────────────────────────────────────────────────
    @app.callback(
        Output('c-es-bidding', 'figure'),
        Input('contr-site-filter',    'value'),
        Input('contr-company-filter', 'value'),
    )
    def es_bidding(site, company):
        df = get_df(site, company)
        if df.empty:
            return go.Figure()

        counts = df['es_in_bidding'].value_counts()
        colors = [C['success'] if l == 'Yes' else C['danger'] for l in counts.index]

        fig = go.Figure(go.Pie(
            labels=counts.index, values=counts.values,
            hole=0.55, marker_colors=colors,
            textinfo='label+value',
            textfont=dict(size=12, family='Nunito, sans-serif'),
            showlegend=False,
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Nunito, sans-serif', size=13, color=C['primary']),
            margin=dict(l=10, r=10, t=10, b=10),
            hoverlabel=dict(bgcolor=C['primary'], bordercolor=C['border'],
                            font=dict(family='Nunito, sans-serif', size=13,
                                      color='#FFFFFF')),
        )
        return fig

    # ── PAYMENT FREQUENCY ─────────────────────────────────────────────────────
    @app.callback(
        Output('c-payment', 'figure'),
        Input('contr-site-filter',    'value'),
        Input('contr-company-filter', 'value'),
    )
    def payment(site, company):
        df = get_df(site, company)
        if df.empty:
            return go.Figure()
        counts = df['payment_frequency'].value_counts()
        fig = go.Figure(go.Pie(
            labels=counts.index, values=counts.values,
            hole=0.55, marker_colors=PALETTE[:len(counts)],
            textinfo='label+value',
            textfont=dict(size=12, family='Nunito, sans-serif'),
            showlegend=False,
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Nunito, sans-serif', size=13, color=C['primary']),
            margin=dict(l=10, r=10, t=10, b=10),
            hoverlabel=dict(bgcolor=C['primary'], bordercolor=C['border'],
                            font=dict(family='Nunito, sans-serif', size=13,
                                      color='#FFFFFF')),
        )
        return fig

    # ── WOMEN BY SITE ─────────────────────────────────────────────────────────
    @app.callback(
        Output('c-women-site', 'figure'),
        Input('contr-site-filter',    'value'),
        Input('contr-company-filter', 'value'),
    )
    def women_site(site, company):
        df = get_df(site, company)
        if df.empty:
            return go.Figure()
        data = df[['site_name', 'women_percent', 'current_women', 'current_workers']]\
            .sort_values('women_percent', ascending=True)
        colors = [C['success'] if v >= 30 else (C['warning'] if v >= 20 else C['danger'])
                  for v in data['women_percent']]

        fig = go.Figure(go.Bar(
            y=data['site_name'], x=data['women_percent'],
            orientation='h', marker_color=colors, marker_line_width=0,
            text=[f'{v:.0f}% ({int(w)}/{int(t)})'
                  for v, w, t in zip(data['women_percent'],
                                     data['current_women'],
                                     data['current_workers'])],
            textposition='outside', textfont=dict(size=11),
        ))
        fig.add_vline(x=30, line_dash='dot', line_color=C['accent'],
                      annotation_text='30% target',
                      annotation_font=dict(size=11, color=C['accent']))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_xaxes(range=[0, 75], ticksuffix='%', title='% Women (Current Workers)')
        return fig

    # ── LOCAL BY SITE ─────────────────────────────────────────────────────────
    @app.callback(
        Output('c-local-site', 'figure'),
        Input('contr-site-filter',    'value'),
        Input('contr-company-filter', 'value'),
    )
    def local_site(site, company):
        df = get_df(site, company)
        if df.empty:
            return go.Figure()
        data = df[['site_name', 'local_percent', 'total_local', 'total_nonlocal',
                   'total_workers']].sort_values('local_percent', ascending=True)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Local',
            y=data['site_name'], x=data['total_local'],
            orientation='h', marker_color=C['success'], marker_line_width=0,
        ))
        fig.add_trace(go.Bar(
            name='Non-Local',
            y=data['site_name'], x=data['total_nonlocal'],
            orientation='h', marker_color=C['danger'], marker_line_width=0,
        ))
        fig.update_layout(**BASE_LAYOUT, barmode='stack')
        fig.update_xaxes(title='Number of Workers')
        return fig

    # ── TOTAL VS CURRENT WORKERS ───────────────────────────────────────────────
    @app.callback(
        Output('c-workers-total-current', 'figure'),
        Input('contr-site-filter',    'value'),
        Input('contr-company-filter', 'value'),
    )
    def workers_total_current(site, company):
        df = get_df(site, company)
        if df.empty:
            return go.Figure()

        df2 = df.copy()
        df2['retention_pct'] = (df2['current_workers'] / df2['total_workers'] * 100).clip(upper=100)
        df2['label'] = df2.apply(
            lambda r: f"{int(r['current_workers'])} / {int(r['total_workers'])} ({r['retention_pct']:.0f}%)",
            axis=1
        )
        df2 = df2.sort_values('retention_pct', ascending=True)

        colors = [C['success'] if v >= 50 else (C['warning'] if v >= 20 else C['danger'])
                  for v in df2['retention_pct']]

        fig = go.Figure(go.Bar(
            y=df2['site_name'],
            x=df2['retention_pct'],
            orientation='h',
            marker_color=colors, marker_line_width=0,
            text=df2['label'],
            textposition='outside',
            textfont=dict(size=11),
        ))
        fig.add_vline(x=50, line_dash='dot', line_color=C['muted'],
                      annotation_text='50%',
                      annotation_font=dict(size=11, color=C['muted']))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_xaxes(range=[0, 145], ticksuffix='%',
                         title='% Workers Still Active (current / total mobilized)')
        return fig

    # ── GENDER SPLIT ─────────────────────────────────────────────────────────
    @app.callback(
        Output('c-gender-split', 'figure'),
        Input('contr-site-filter',    'value'),
        Input('contr-company-filter', 'value'),
    )
    def gender_split(site, company):
        df = get_df(site, company)
        if df.empty:
            return go.Figure()
        total_men   = int(df['current_men'].sum())
        total_women = int(df['current_women'].sum())

        fig = go.Figure(go.Pie(
            labels=['Men', 'Women'],
            values=[total_men, total_women],
            hole=0.55,
            marker_colors=[C['accent'], C['secondary']],
            textinfo='label+percent+value',
            textfont=dict(size=12, family='Nunito, sans-serif'),
            showlegend=False,
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Nunito, sans-serif', size=13, color=C['primary']),
            margin=dict(l=10, r=10, t=10, b=10),
            hoverlabel=dict(bgcolor=C['primary'], bordercolor=C['border'],
                            font=dict(family='Nunito, sans-serif', size=13,
                                      color='#FFFFFF')),
        )
        return fig

    # ── INCIDENTS ─────────────────────────────────────────────────────────────
    @app.callback(
        Output('c-incidents', 'figure'),
        Input('contr-site-filter',    'value'),
        Input('contr-company-filter', 'value'),
    )
    def incidents(site, company):
        df = get_df(site, company)
        if df.empty:
            return go.Figure()

        # Build single unified bar chart — all sites, color by incident status
        df_sorted = df.copy()
        df_sorted['inc_count_plot'] = df_sorted.apply(
            lambda r: float(r['incidents_count']) if r['incidents_occurred'] == 'Yes'
                      else 0.0, axis=1
        ).fillna(0.5)  # 0.5 = had incident but count unknown
        df_sorted['inc_label'] = df_sorted.apply(
            lambda r: f"{int(r['incidents_count'])} incident(s)"
                      if r['incidents_occurred'] == 'Yes' and not pd.isna(r['incidents_count'])
                      else ('⚠ Incident (n/a)' if r['incidents_occurred'] == 'Yes'
                            else '✓ None'),
            axis=1
        )
        df_sorted = df_sorted.sort_values('inc_count_plot', ascending=True)

        colors = [C['danger'] if r == 'Yes' else C['success']
                  for r in df_sorted['incidents_occurred']]

        fig = go.Figure(go.Bar(
            y=df_sorted['site_name'],
            x=df_sorted['inc_count_plot'],
            orientation='h',
            marker_color=colors, marker_line_width=0,
            text=df_sorted['inc_label'],
            textposition='outside',
            textfont=dict(size=12),
        ))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_xaxes(title='Number of Incidents', range=[0, 10])
        return fig

    # ── PPE FREQUENCY ─────────────────────────────────────────────────────────
    @app.callback(
        Output('c-ppe-freq', 'figure'),
        Input('contr-site-filter',    'value'),
        Input('contr-company-filter', 'value'),
    )
    def ppe_freq(site, company):
        df = get_df(site, company)
        if df.empty:
            return go.Figure()
        counts = df['ppe_frequency'].value_counts()
        color_map = {
            'More than twice':    C['success'],
            'Once (a month)':     C['warning'],
            'Once (a quarter)':   C['danger'],
        }
        colors = [color_map.get(l, C['muted']) for l in counts.index]

        fig = go.Figure(go.Pie(
            labels=counts.index, values=counts.values,
            hole=0.55, marker_colors=colors,
            textinfo='label+value',
            textfont=dict(size=11, family='Nunito, sans-serif'),
            showlegend=False,
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Nunito, sans-serif', size=13, color=C['primary']),
            margin=dict(l=10, r=10, t=10, b=10),
            hoverlabel=dict(bgcolor=C['primary'], bordercolor=C['border'],
                            font=dict(family='Nunito, sans-serif', size=13,
                                      color='#FFFFFF')),
        )
        return fig

    # ── PPE TYPES ─────────────────────────────────────────────────────────────
    @app.callback(
        Output('c-ppe-types', 'figure'),
        Input('contr-site-filter',    'value'),
        Input('contr-company-filter', 'value'),
    )
    def ppe_types(site, company):
        df = get_df(site, company)
        if df.empty:
            return go.Figure()
        n = len(df)
        ppe_map = {
            'ppe_helmet':       'Helmet',
            'ppe_gloves':       'Gloves',
            'ppe_safety_shoes': 'Safety Shoes',
            'ppe_mask':         'Mask',
            'ppe_earplug':      'Earplugs',
        }
        vals   = [int(df[col].sum()) for col in ppe_map]
        pcts   = [v / n * 100 for v in vals]
        colors = [C['success'] if p == 100 else (C['warning'] if p >= 80 else C['danger'])
                  for p in pcts]

        fig = go.Figure(go.Bar(
            x=list(ppe_map.values()), y=pcts,
            marker_color=colors, marker_line_width=0,
            text=[f'{v}/{n}' for v in vals],
            textposition='outside', textfont=dict(size=11),
        ))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_xaxes(tickangle=-20)
        fig.update_yaxes(title='% of Sites', ticksuffix='%', range=[0, 120])
        return fig

    # ── TRAINING COVERAGE ─────────────────────────────────────────────────────
    @app.callback(
        Output('c-training-coverage', 'figure'),
        Input('contr-site-filter',    'value'),
        Input('contr-company-filter', 'value'),
    )
    def training_coverage(site, company):
        df = get_df(site, company)
        if df.empty:
            return go.Figure()
        data = df[['site_name', 'training_coverage']]\
            .sort_values('training_coverage', ascending=True)
        colors = [C['success'] if v >= 30 else (C['warning'] if v >= 10 else C['danger'])
                  for v in data['training_coverage']]

        fig = go.Figure(go.Bar(
            y=data['site_name'], x=data['training_coverage'],
            orientation='h', marker_color=colors, marker_line_width=0,
            text=[f'{v:.1f}%' for v in data['training_coverage']],
            textposition='outside', textfont=dict(size=11),
        ))
        fig.add_vline(x=30, line_dash='dot', line_color=C['accent'],
                      annotation_text='30% target',
                      annotation_font=dict(size=11, color=C['accent']))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_xaxes(range=[0, 75], ticksuffix='%', title='% Workers Trained')
        return fig

    # ── TRAINING NUMBERS ──────────────────────────────────────────────────────
    @app.callback(
        Output('c-training-numbers', 'figure'),
        Input('contr-site-filter',    'value'),
        Input('contr-company-filter', 'value'),
    )
    def training_numbers(site, company):
        df = get_df(site, company)
        if df.empty:
            return go.Figure()
        data = df[['site_name', 'training_exact_number', 'total_workers']]\
            .sort_values('total_workers', ascending=False)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Total Workers',
            x=data['site_name'],
            y=data['total_workers'],
            marker_color=C['border'], marker_line_width=0,
        ))
        fig.add_trace(go.Bar(
            name='Workers Trained',
            x=data['site_name'],
            y=data['training_exact_number'].fillna(0),
            marker_color=C['secondary'], marker_line_width=0,
        ))
        fig.update_layout(**BASE_LAYOUT, barmode='group')
        fig.update_xaxes(tickangle=-30)
        fig.update_yaxes(title='Number of Workers')
        return fig

    # ── WASTE DISPOSAL ────────────────────────────────────────────────────────
    @app.callback(
        Output('c-waste', 'figure'),
        Input('contr-site-filter',    'value'),
        Input('contr-company-filter', 'value'),
    )
    def waste(site, company):
        df = get_df(site, company)
        if df.empty:
            return go.Figure()
        counts = df['waste_disposal_location'].value_counts()
        fig = go.Figure(go.Pie(
            labels=counts.index, values=counts.values,
            hole=0.55, marker_colors=PALETTE[:len(counts)],
            textinfo='label+value',
            textfont=dict(size=12, family='Nunito, sans-serif'),
            showlegend=False,
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Nunito, sans-serif', size=13, color=C['primary']),
            margin=dict(l=10, r=10, t=10, b=10),
            hoverlabel=dict(bgcolor=C['primary'], bordercolor=C['border'],
                            font=dict(family='Nunito, sans-serif', size=13,
                                      color='#FFFFFF')),
        )
        return fig

    # ── COMPLIANCE INDICATORS ─────────────────────────────────────────────────
    @app.callback(
        Output('c-compliance', 'figure'),
        Input('contr-site-filter',    'value'),
        Input('contr-company-filter', 'value'),
    )
    def compliance(site, company):
        df = get_df(site, company)
        if df.empty:
            return go.Figure()
        n    = len(df)
        vals = [int(df[c].eq('Yes').sum()) for c in COMP_BOOL_COLS]
        pcts = [v / n * 100 for v in vals]
        colors = [C['success'] if p == 100 else (C['warning'] if p >= 80 else C['danger'])
                  for p in pcts]

        fig = go.Figure(go.Bar(
            y=COMP_LABELS, x=pcts, orientation='h',
            marker_color=colors, marker_line_width=0,
            text=[f'{v}/{n} ({p:.0f}%)' for v, p in zip(vals, pcts)],
            textposition='outside', textfont=dict(size=12),
        ))
        fig.add_vline(x=100, line_dash='dot', line_color=C['muted'],
                      annotation_text='100% required',
                      annotation_font=dict(size=11, color=C['muted']))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_xaxes(range=[0, 125], ticksuffix='%')
        return fig

    # ── COMPLIANCE FLAGS ──────────────────────────────────────────────────────
    @app.callback(
        Output('c-compliance-flags', 'children'),
        Input('contr-site-filter',    'value'),
        Input('contr-company-filter', 'value'),
    )
    def compliance_flags(site, company):
        df = get_df(site, company)
        if df.empty:
            return html.Div('—')
        n = len(df)
        indicators = [
            ('Missing E&S Instrument',   int(df[INST_COLS].eq(0).any(axis=1).sum())),
            ('No GRM Logbook',           int(df['grm_logbook'].eq('No').sum())),
            ('No Chance Finds Proc.',    int(df['chance_finds_procedure'].eq('No').sum())),
            ('No Waste Authorization',   int(df['waste_disposal_auth'].eq('No').sum())),
            ('No E&S in Bidding',        int(df['es_in_bidding'].eq('No').sum())),
            ('No Social Specialist',     int(df['staff_social_specialist'].eq(0).sum())),
            ('Has Incidents',            int(df['incidents_occurred'].eq('Yes').sum())),
        ]
        items = []
        for label, count in indicators:
            pct   = count / n * 100
            color = C['success'] if count == 0 else \
                    (C['warning'] if pct < 25 else C['danger'])
            items.append(html.Div([
                html.Div([
                    html.Span(label, style={
                        'fontSize': '13px', 'fontWeight': '600',
                        'color': C['primary'],
                    }),
                    html.Span(f'{count}/{n}', style={
                        'fontSize': '13px', 'fontWeight': '800', 'color': color,
                    }),
                ], style={'display': 'flex', 'justifyContent': 'space-between',
                          'marginBottom': '4px'}),
                html.Div([
                    html.Div(style={
                        'width': f'{min(pct, 100):.0f}%', 'height': '5px',
                        'background': color, 'borderRadius': '3px',
                    }),
                ], style={'background': C['border'], 'borderRadius': '3px',
                          'overflow': 'hidden'}),
            ], style={'marginBottom': '13px'}))
        return html.Div(items)

    # ── SCORING TABLE ─────────────────────────────────────────────────────────
    @app.callback(
        Output('c-scoring-table', 'children'),
        Input('contr-site-filter',    'value'),
        Input('contr-company-filter', 'value'),
    )
    def scoring_table(site, company):
        df = get_df(site, company)
        if df.empty:
            return html.Div('No data available.')

        data = df.sort_values('global_score', ascending=False)

        rows = []
        for _, r in data.iterrows():
            gc, gb = score_color(float(r['global_score']))

            rows.append(html.Tr([
                html.Td([
                    html.Div(r['site_name'], style={
                        'fontWeight': '700', 'fontSize': '12px',
                        'color': C['primary'], 'marginBottom': '2px',
                    }),
                    html.Div(r['company_clean'], style={
                        'fontSize': '10px', 'color': C['muted'],
                    }),
                ], style={'padding': '10px 12px', 'minWidth': '160px'}),
                # Instruments
                html.Td(prog_bar(r['inst_score'],
                                 score_color(float(r['inst_score']))[0]),
                        style={'padding': '10px 8px'}),
                # Compliance
                html.Td(prog_bar(r['comp_score'],
                                 score_color(float(r['comp_score']))[0]),
                        style={'padding': '10px 8px'}),
                # Training
                html.Td(prog_bar(min(float(r['training_coverage']), 100),
                                 score_color(float(r['training_coverage']))[0]),
                        style={'padding': '10px 8px'}),
                # Women %
                html.Td(prog_bar(min(float(r['women_percent']), 50) / 50 * 100,
                                 score_color(float(r['women_percent']) / 30 * 100)[0]),
                        style={'padding': '10px 8px'}),
                # Local %
                html.Td(prog_bar(float(r['local_percent']),
                                 score_color(float(r['local_percent']))[0]),
                        style={'padding': '10px 8px'}),
                # Incidents
                html.Td(
                    html.Span(
                        f"{int(r['incidents_count'])} incidents" if r['incidents_occurred'] == 'Yes'
                        else '✓ None',
                        style={
                            'fontSize': '12px', 'fontWeight': '700',
                            'color': C['danger'] if r['incidents_occurred'] == 'Yes'
                                     else C['success'],
                        }
                    ),
                    style={'padding': '10px 8px', 'textAlign': 'center'},
                ),
                # Global score
                html.Td(
                    html.Span(f'{float(r["global_score"]):.0f}%', style={
                        'background': gb, 'color': gc,
                        'padding': '4px 12px', 'borderRadius': '12px',
                        'fontSize': '13px', 'fontWeight': '900',
                    }),
                    style={'padding': '10px 12px', 'textAlign': 'center'},
                ),
            ], style={
                'borderBottom': f'1px solid {C["border"]}',
                'background': '#FFEBEE' if float(r['global_score']) < 50 else 'white',
            }))

        headers = ['Site / Company', 'Instruments (30%)', 'Compliance (30%)',
                   'Training (20%)', 'Women (10%)', 'Local (10%)',
                   'Incidents', 'Global Score']

        return html.Table([
            html.Thead(html.Tr([
                html.Th(h, style={
                    'padding': '10px 12px', 'fontSize': '11px', 'fontWeight': '700',
                    'textTransform': 'uppercase', 'letterSpacing': '1px',
                    'color': C['muted'], 'background': C['light_bg'],
                    'borderBottom': f'2px solid {C["border"]}',
                    'textAlign': 'left' if i == 0 else 'center',
                    'whiteSpace': 'nowrap',
                }) for i, h in enumerate(headers)
            ])),
            html.Tbody(rows),
        ], style={'width': '100%', 'borderCollapse': 'collapse', 'fontSize': '13px'})