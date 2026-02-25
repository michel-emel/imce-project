"""
IMCE Dashboard — GRC Page (Grievance Redress Committees)
Filters: District → Sector → Cell
Sections: KPIs, Complaint Performance, Types, Escalations,
          Resolution Time, Capacity & Resources, Scoring Table
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

COMP_COLS = [
    'complaint_late_payment', 'complaint_valuation_error',
    'complaint_household_conflict', 'complaint_valuation_refusal', 'complaint_other',
]
COMP_LABELS = [
    'Late Payment', 'Valuation Error',
    'Household Conflict', 'Valuation Refusal', 'Other',
]

FACIL_COLS   = ['facil_materials', 'facil_transport',
                'facil_communication', 'facil_per_diem', 'facil_other']
FACIL_LABELS = ['Materials', 'Transport', 'Communication', 'Per Diem', 'Other']

# ─────────────────────────────────────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────────────────────────────────────

def load_grc():
    import os
    paths = [
        'GRC_clean.csv',
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'GRC_clean.csv'),
    ]
    df = pd.DataFrame()
    for p in paths:
        if os.path.exists(p):
            df = pd.read_csv(p)
            break
    if df.empty:
        return df

    # Normalize casing
    df['district'] = df['district'].str.strip().str.title()
    df['sector']   = df['sector'].str.strip().str.title()
    df['cell']     = df['cell'].str.strip().str.title()

    # Derived metrics
    df['resolution_rate'] = (
        df['complaints_resolved'] / df['complaints_received'].replace(0, np.nan) * 100
    ).fillna(0).clip(upper=100)

    df['escalation_rate'] = (
        df['complaints_escalated'] / df['complaints_received'].replace(0, np.nan) * 100
    ).fillna(0).clip(upper=100)

    df['pending_rate'] = (
        df['complaints_pending'] / df['complaints_received'].replace(0, np.nan) * 100
    ).fillna(0).clip(upper=100)

    # Facility score (0-100)
    df['facil_score'] = df[FACIL_COLS].sum(axis=1) / len(FACIL_COLS) * 100

    # Complaint type count
    df['complaint_type_count'] = df[COMP_COLS].sum(axis=1)

    # Resolution time category
    def cat_resolution(t):
        t = str(t).lower()
        if 'day' in t:
            return 'Within 1 day'
        elif 'week' in t and 'month' not in t:
            return '1 week'
        elif 'month' in t:
            return '1 month'
        elif 'no complaint' in t:
            return 'No complaints'
        return 'Variable'
    df['resolution_cat'] = df['complaint_resolution_time'].apply(cat_resolution)

    # Global performance score
    # Resolution (40%) + Training (20%) + Facilities (20%) + Low escalation (20%)
    df['train_score'] = df['training_count'] / 3 * 100  # max 3
    df['esc_score']   = (100 - df['escalation_rate']).clip(lower=0)
    df['global_score'] = (
        df['resolution_rate'] * 0.40 +
        df['train_score']     * 0.20 +
        df['facil_score']     * 0.20 +
        df['esc_score']       * 0.20
    )

    return df


GRC = load_grc()


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


def score_color(pct):
    if pct >= 75:
        return C['success'], '#E8F5E9'
    elif pct >= 50:
        return C['warning'], '#FFF3E0'
    return C['danger'], '#FFEBEE'


def prog_bar(pct, color):
    return html.Div([
        html.Div([
            html.Div(style={
                'width': f'{min(float(pct), 100):.0f}%',
                'height': '6px', 'background': color, 'borderRadius': '3px',
            }),
        ], style={
            'background': C['border'], 'borderRadius': '3px', 'overflow': 'hidden',
            'width': '80px', 'display': 'inline-block',
            'verticalAlign': 'middle', 'marginRight': '6px',
        }),
        html.Span(f'{float(pct):.0f}%', style={
            'fontSize': '12px', 'fontWeight': '700',
            'color': color, 'verticalAlign': 'middle',
        }),
    ])


def get_df(district, sector, cell):
    df = GRC.copy()
    if df.empty:
        return df
    if district and district != 'ALL':
        df = df[df['district'] == district]
    if sector and sector != 'ALL':
        df = df[df['sector'] == sector]
    if cell and cell != 'ALL':
        df = df[df['cell'] == cell]
    return df


# ─────────────────────────────────────────────────────────────────────────────
# FILTER BAR
# ─────────────────────────────────────────────────────────────────────────────

def filter_bar():
    districts = sorted(GRC['district'].unique().tolist()) if not GRC.empty else []
    dd  = {'width': '200px', 'fontFamily': 'Nunito, sans-serif', 'fontSize': '13px'}
    lbl = {
        'fontSize': '11px', 'fontWeight': '700', 'textTransform': 'uppercase',
        'letterSpacing': '1px', 'color': C['muted'], 'marginBottom': '4px',
        'display': 'block',
    }
    return html.Div([
        html.Div([
            html.Label('District', style=lbl),
            dcc.Dropdown(
                id='grc-district-filter',
                options=[{'label': 'All Districts', 'value': 'ALL'}] +
                        [{'label': d, 'value': d} for d in districts],
                value='ALL', clearable=False, style=dd,
            ),
        ]),
        html.Div([
            html.Label('Sector', style=lbl),
            dcc.Dropdown(
                id='grc-sector-filter',
                options=[{'label': 'All Sectors', 'value': 'ALL'}],
                value='ALL', clearable=False, style=dd,
            ),
        ]),
        html.Div([
            html.Label('Cell', style=lbl),
            dcc.Dropdown(
                id='grc-cell-filter',
                options=[{'label': 'All Cells', 'value': 'ALL'}],
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
    if GRC.empty:
        return html.Div('GRC_clean.csv not found.',
                        style={'padding': '40px 40px 40px 260px'})

    total_received = int(GRC['complaints_received'].sum())
    avg_resolution = float(GRC[GRC['complaints_received'] > 0]['resolution_rate'].mean())

    if avg_resolution >= 75:
        sc, st, sb = C['success'], '● ON TRACK', '#E8F5E9'
    elif avg_resolution >= 50:
        sc, st, sb = C['warning'], '● ATTENTION REQUIRED', '#FFF3E0'
    else:
        sc, st, sb = C['danger'], '● CRITICAL', '#FFEBEE'

    return html.Div([

        # PAGE HEADER
        html.Div([
            html.Div([
                html.H2('Grievance Redress Committees', style={
                    'margin': '0 0 4px 0', 'fontWeight': '900',
                    'fontSize': '26px', 'color': C['primary'],
                }),
                html.P(
                    f'{len(GRC)} GRCs across {GRC["district"].nunique()} districts — '
                    f'{total_received} total complaints received — IMCE Project Rwanda',
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
            dbc.Col(html.Div(id='g-kpi-total'),      md=2),
            dbc.Col(html.Div(id='g-kpi-received'),   md=2),
            dbc.Col(html.Div(id='g-kpi-resolved'),   md=2),
            dbc.Col(html.Div(id='g-kpi-pending'),    md=2),
            dbc.Col(html.Div(id='g-kpi-escalated'),  md=2),
            dbc.Col(html.Div(id='g-kpi-inactive'),   md=2),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 2 — Complaint performance
        dbc.Row([
            dbc.Col([card([
                section_title('Complaints Funnel',
                              'From reception to resolution — where do complaints get stuck?'),
                dcc.Graph(id='g-funnel',
                          config={'displayModeBar': False}, style={'height': '300px'}),
            ])], md=4),
            dbc.Col([card([
                section_title('Resolution Rate by GRC',
                              'Percentage of received complaints successfully resolved — critical GRCs highlighted'),
                dcc.Graph(id='g-resolution-rate',
                          config={'displayModeBar': False}, style={'height': '300px'}),
            ])], md=8),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 3 — Complaint volume details
        dbc.Row([
            dbc.Col([card([
                section_title('Complaint Volume by GRC',
                              'Received, resolved, pending and escalated per GRC'),
                dcc.Graph(id='g-volume',
                          config={'displayModeBar': False}, style={'height': '320px'}),
            ])], md=8),
            dbc.Col([card([
                section_title('Complaint Types',
                              'Which types of complaints are most frequent across all GRCs?'),
                dcc.Graph(id='g-complaint-types',
                          config={'displayModeBar': False}, style={'height': '320px'}),
            ])], md=4),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 4 — Complaint types per GRC
        dbc.Row([
            dbc.Col([card([
                section_title('Complaint Types by GRC',
                              'Which GRCs are dealing with which types of complaints?'),
                dcc.Graph(id='g-types-per-grc',
                          config={'displayModeBar': False}, style={'height': '300px'}),
            ])], md=12),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 5 — Escalation & Pending
        dbc.Row([
            dbc.Col([card([
                section_title('Escalation Rate by GRC',
                              '% of complaints escalated to higher authority — NYABISIMDU at 77% is critical'),
                dcc.Graph(id='g-escalation-rate',
                          config={'displayModeBar': False}, style={'height': '280px'}),
            ])], md=5),
            dbc.Col([card([
                section_title('Where Are Complaints Escalated?',
                              'Which authorities receive escalated complaints?'),
                dcc.Graph(id='g-escalated-to',
                          config={'displayModeBar': False}, style={'height': '280px'}),
            ])], md=3),
            dbc.Col([card([
                section_title('Pending Complaints — Why?',
                              'Main reasons why complaints remain unresolved'),
                html.Div(id='g-pending-reasons'),
            ])], md=4),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 6 — Resolution time
        dbc.Row([
            dbc.Col([card([
                section_title('Declared Resolution Time',
                              'How quickly do GRCs say they resolve complaints?'),
                dcc.Graph(id='g-resolution-time',
                          config={'displayModeBar': False}, style={'height': '260px'}),
            ])], md=4),
            dbc.Col([card([
                section_title('Resolution Time vs Actual Resolution Rate',
                              'Do GRCs that claim fast resolution actually perform better?'),
                dcc.Graph(id='g-time-vs-rate',
                          config={'displayModeBar': False}, style={'height': '260px'}),
            ])], md=8),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 7 — Capacity & resources
        dbc.Row([
            dbc.Col([card([
                section_title('Facilities Available per GRC',
                              'Materials, transport, communication, per diem — who has what?'),
                dcc.Graph(id='g-facilities',
                          config={'displayModeBar': False}, style={'height': '280px'}),
            ])], md=6),
            dbc.Col([card([
                section_title('Facility Coverage vs Resolution Rate',
                              'GRCs with more resources — do they resolve better?'),
                dcc.Graph(id='g-facil-vs-resolution',
                          config={'displayModeBar': False}, style={'height': '280px'}),
            ])], md=6),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 8 — Scoring table
        dbc.Row([
            dbc.Col([card([
                section_title('GRC Performance Scoring Dashboard',
                              'Composite score: Resolution Rate (40%) + Training (20%) + Facilities (20%) + Low Escalation (20%)'),
                html.Div(id='g-scoring-table'),
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

    # ── CASCADE: sector options ───────────────────────────────────────────────
    @app.callback(
        Output('grc-sector-filter', 'options'),
        Output('grc-sector-filter', 'value'),
        Input('grc-district-filter', 'value'),
    )
    def update_sector_options(district):
        df = GRC.copy()
        if district and district != 'ALL':
            df = df[df['district'] == district]
        sectors = sorted(df['sector'].dropna().unique().tolist())
        options = [{'label': 'All Sectors', 'value': 'ALL'}] + \
                  [{'label': s, 'value': s} for s in sectors]
        return options, 'ALL'

    # ── CASCADE: cell options ─────────────────────────────────────────────────
    @app.callback(
        Output('grc-cell-filter', 'options'),
        Output('grc-cell-filter', 'value'),
        Input('grc-district-filter', 'value'),
        Input('grc-sector-filter',   'value'),
    )
    def update_cell_options(district, sector):
        df = GRC.copy()
        if district and district != 'ALL':
            df = df[df['district'] == district]
        if sector and sector != 'ALL':
            df = df[df['sector'] == sector]
        cells = sorted(df['cell'].dropna().unique().tolist())
        options = [{'label': 'All Cells', 'value': 'ALL'}] + \
                  [{'label': c, 'value': c} for c in cells]
        return options, 'ALL'

    # ── KPIs ─────────────────────────────────────────────────────────────────
    @app.callback(
        Output('g-kpi-total',     'children'),
        Output('g-kpi-received',  'children'),
        Output('g-kpi-resolved',  'children'),
        Output('g-kpi-pending',   'children'),
        Output('g-kpi-escalated', 'children'),
        Output('g-kpi-inactive',  'children'),
        Input('grc-district-filter', 'value'),
        Input('grc-sector-filter',   'value'),
        Input('grc-cell-filter',     'value'),
    )
    def update_kpis(district, sector, cell):
        df = get_df(district, sector, cell)
        if df.empty:
            return [html.Div('—')] * 6

        n          = len(df)
        received   = int(df['complaints_received'].sum())
        resolved   = int(df['complaints_resolved'].sum())
        pending    = int(df['complaints_pending'].sum())
        escalated  = int(df['complaints_escalated'].sum())
        inactive   = int((df['complaints_received'] == 0).sum())
        active_df  = df[df['complaints_received'] > 0]
        avg_res    = float(active_df['resolution_rate'].mean()) if len(active_df) > 0 else 0

        rc = C['success'] if avg_res >= 75 else (C['warning'] if avg_res >= 50 else C['danger'])
        pc = C['danger']  if pending > 10 else (C['warning'] if pending > 0 else C['success'])
        ec = C['danger']  if escalated > received * 0.3 else \
             (C['warning'] if escalated > 0 else C['success'])

        return (
            kpi('GRCs Active', str(n),
                f'{df["district"].nunique()} districts covered', C['accent']),
            kpi('Complaints Received', str(received),
                f'Across {n} GRC locations', C['p3']),
            kpi('Resolution Rate', f'{avg_res:.0f}%',
                f'{resolved} complaints resolved', rc),
            kpi('Pending Complaints', str(pending),
                'Awaiting resolution', pc),
            kpi('Escalated Complaints', str(escalated),
                'Sent to higher authority', ec),
            kpi('GRCs with 0 Complaints', str(inactive),
                'No complaints received yet', C['muted']),
        )

    # ── FUNNEL ────────────────────────────────────────────────────────────────
    @app.callback(
        Output('g-funnel', 'figure'),
        Input('grc-district-filter', 'value'),
        Input('grc-sector-filter',   'value'),
        Input('grc-cell-filter',     'value'),
    )
    def funnel(district, sector, cell):
        df = get_df(district, sector, cell)
        if df.empty:
            return go.Figure()

        received  = int(df['complaints_received'].sum())
        resolved  = int(df['complaints_resolved'].sum())
        escalated = int(df['complaints_escalated'].sum())
        pending   = int(df['complaints_pending'].sum())

        fig = go.Figure(go.Funnel(
            y=['Received', 'Resolved', 'Escalated', 'Still Pending'],
            x=[received, resolved, escalated, pending],
            textinfo='value+percent initial',
            marker_color=[C['accent'], C['success'], C['warning'], C['danger']],
            connector=dict(line=dict(color=C['border'], width=1.5)),
            textfont=dict(family='Nunito, sans-serif', size=12),
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Nunito, sans-serif', color=C['primary'], size=13),
            margin=dict(l=10, r=60, t=10, b=10), showlegend=False,
            hoverlabel=dict(bgcolor=C['primary'], bordercolor=C['border'],
                            font=dict(family='Nunito, sans-serif', size=13,
                                      color='#FFFFFF')),
        )
        return fig

    # ── RESOLUTION RATE ───────────────────────────────────────────────────────
    @app.callback(
        Output('g-resolution-rate', 'figure'),
        Input('grc-district-filter', 'value'),
        Input('grc-sector-filter',   'value'),
        Input('grc-cell-filter',     'value'),
    )
    def resolution_rate(district, sector, cell):
        df = get_df(district, sector, cell)
        if df.empty:
            return go.Figure()

        data = df[['grc_location', 'resolution_rate', 'complaints_received',
                   'complaints_resolved']].sort_values('resolution_rate', ascending=True)

        colors = [C['success'] if v >= 75 else (C['warning'] if v >= 50 else C['danger'])
                  for v in data['resolution_rate']]

        fig = go.Figure(go.Bar(
            y=data['grc_location'],
            x=data['resolution_rate'],
            orientation='h',
            marker_color=colors, marker_line_width=0,
            text=[f'{v:.0f}% ({int(r)}/{int(t)})'
                  for v, r, t in zip(data['resolution_rate'],
                                     data['complaints_resolved'],
                                     data['complaints_received'])],
            textposition='outside', textfont=dict(size=11),
        ))
        fig.add_vline(x=75, line_dash='dot', line_color=C['muted'],
                      annotation_text='75% target',
                      annotation_font=dict(size=11, color=C['muted']))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_xaxes(range=[0, 130], ticksuffix='%', title='Resolution Rate')
        return fig

    # ── COMPLAINT VOLUME ──────────────────────────────────────────────────────
    @app.callback(
        Output('g-volume', 'figure'),
        Input('grc-district-filter', 'value'),
        Input('grc-sector-filter',   'value'),
        Input('grc-cell-filter',     'value'),
    )
    def volume(district, sector, cell):
        df = get_df(district, sector, cell)
        if df.empty:
            return go.Figure()

        data = df.sort_values('complaints_received', ascending=False)

        fig = go.Figure()
        for col, label, color in [
            ('complaints_resolved',  'Resolved',  C['success']),
            ('complaints_pending',   'Pending',   C['warning']),
            ('complaints_escalated', 'Escalated', C['danger']),
        ]:
            fig.add_trace(go.Bar(
                name=label,
                x=data['grc_location'],
                y=data[col],
                marker_color=color, marker_line_width=0,
                text=data[col],
                textposition='inside',
                textfont=dict(color='white', size=10),
            ))

        fig.update_layout(**BASE_LAYOUT, barmode='stack')
        fig.update_xaxes(tickangle=-25)
        fig.update_yaxes(title='Number of Complaints')
        return fig

    # ── COMPLAINT TYPES ───────────────────────────────────────────────────────
    @app.callback(
        Output('g-complaint-types', 'figure'),
        Input('grc-district-filter', 'value'),
        Input('grc-sector-filter',   'value'),
        Input('grc-cell-filter',     'value'),
    )
    def complaint_types(district, sector, cell):
        df = get_df(district, sector, cell)
        if df.empty:
            return go.Figure()

        n    = len(df)
        vals = [int(df[col].sum()) for col in COMP_COLS]
        pcts = [v / n * 100 for v in vals]

        # Sort by frequency
        sorted_pairs = sorted(zip(COMP_LABELS, vals, pcts),
                              key=lambda x: x[1], reverse=True)
        labels, vals, pcts = zip(*sorted_pairs)

        fig = go.Figure(go.Bar(
            y=list(labels), x=list(vals),
            orientation='h',
            marker_color=PALETTE[:len(labels)], marker_line_width=0,
            text=[f'{v} GRCs ({p:.0f}%)' for v, p in zip(vals, pcts)],
            textposition='outside', textfont=dict(size=11),
        ))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_xaxes(range=[0, n + 3], title='Number of GRCs reporting this type')
        return fig

    # ── TYPES PER GRC ─────────────────────────────────────────────────────────
    @app.callback(
        Output('g-types-per-grc', 'figure'),
        Input('grc-district-filter', 'value'),
        Input('grc-sector-filter',   'value'),
        Input('grc-cell-filter',     'value'),
    )
    def types_per_grc(district, sector, cell):
        df = get_df(district, sector, cell)
        if df.empty:
            return go.Figure()

        data = df.sort_values('complaints_received', ascending=False)

        fig = go.Figure()
        for col, label, color in zip(COMP_COLS, COMP_LABELS, PALETTE):
            fig.add_trace(go.Bar(
                name=label,
                x=data['grc_location'],
                y=data[col],
                marker_color=color, marker_line_width=0,
            ))
        fig.update_layout(**BASE_LAYOUT, barmode='stack')
        fig.update_xaxes(tickangle=-20)
        fig.update_yaxes(title='Complaint Type Present (1=Yes)')
        return fig

    # ── ESCALATION RATE ───────────────────────────────────────────────────────
    @app.callback(
        Output('g-escalation-rate', 'figure'),
        Input('grc-district-filter', 'value'),
        Input('grc-sector-filter',   'value'),
        Input('grc-cell-filter',     'value'),
    )
    def escalation_rate(district, sector, cell):
        df = get_df(district, sector, cell)
        if df.empty:
            return go.Figure()

        data = df[df['complaints_received'] > 0][
            ['grc_location', 'escalation_rate', 'complaints_escalated',
             'complaints_received']
        ].sort_values('escalation_rate', ascending=True)

        colors = [C['danger'] if v >= 50 else (C['warning'] if v >= 20 else C['success'])
                  for v in data['escalation_rate']]

        fig = go.Figure(go.Bar(
            y=data['grc_location'],
            x=data['escalation_rate'],
            orientation='h',
            marker_color=colors, marker_line_width=0,
            text=[f'{v:.0f}% ({int(e)}/{int(r)})'
                  for v, e, r in zip(data['escalation_rate'],
                                     data['complaints_escalated'],
                                     data['complaints_received'])],
            textposition='outside', textfont=dict(size=11),
        ))
        fig.add_vline(x=30, line_dash='dot', line_color=C['muted'],
                      annotation_text='30% alert',
                      annotation_font=dict(size=11, color=C['muted']))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_xaxes(range=[0, 110], ticksuffix='%', title='Escalation Rate')
        return fig

    # ── ESCALATED TO ──────────────────────────────────────────────────────────
    @app.callback(
        Output('g-escalated-to', 'figure'),
        Input('grc-district-filter', 'value'),
        Input('grc-sector-filter',   'value'),
        Input('grc-cell-filter',     'value'),
    )
    def escalated_to(district, sector, cell):
        df = get_df(district, sector, cell)
        if df.empty:
            return go.Figure()

        def simplify(v):
            v = str(v).strip()
            if 'CoK' in v or 'Kigali' in v or 'City' in v:
                return 'City of Kigali'
            elif 'District' in v:
                return 'District Office'
            elif 'Sector' in v:
                return 'Sector'
            elif 'Contractor' in v or 'ECOGEL' in v:
                return 'Contractor'
            elif v in ('nan', 'None', ''):
                return None
            return 'Other'

        vals = df['escalated_to'].apply(simplify).dropna()
        if vals.empty:
            return go.Figure()

        counts = vals.value_counts()
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

    # ── PENDING REASONS ───────────────────────────────────────────────────────
    @app.callback(
        Output('g-pending-reasons', 'children'),
        Input('grc-district-filter', 'value'),
        Input('grc-sector-filter',   'value'),
        Input('grc-cell-filter',     'value'),
    )
    def pending_reasons(district, sector, cell):
        df = get_df(district, sector, cell)
        reasons = df[df['pending_reason'].notna()][
            ['grc_location', 'pending_reason', 'complaints_pending']
        ]

        if reasons.empty:
            return html.Div([
                html.Span('✓', style={'fontSize': '24px', 'color': C['success']}),
                html.P('No pending complaints in this selection.',
                       style={'color': C['success'], 'fontWeight': '700',
                              'fontSize': '13px', 'margin': '6px 0 0 0'}),
            ], style={'textAlign': 'center', 'padding': '24px'})

        def categorize(text):
            t = str(text).lower()
            if 'new' in t:
                return '🆕 New complaints'
            elif 'valuation' in t or 'counter' in t:
                return '💰 Counter valuation dispute'
            elif 'abroad' in t or 'outside' in t or 'soldier' in t:
                return '🌍 Beneficiary unreachable'
            elif 'contractor' in t or 'road' in t or 'complet' in t:
                return '🏗️ Awaiting project completion'
            elif 'cok' in t or 'city' in t:
                return '🏛️ Pending city-level decision'
            return '❓ Other'

        items = []
        for _, r in reasons.iterrows():
            cat = categorize(r['pending_reason'])
            items.append(html.Div([
                html.Div([
                    html.Span(cat, style={
                        'fontSize': '12px', 'fontWeight': '700',
                        'color': C['warning'],
                    }),
                    html.Span(f'{int(r["complaints_pending"])} pending', style={
                        'fontSize': '11px', 'color': C['danger'],
                        'fontWeight': '800',
                    }),
                ], style={'display': 'flex', 'justifyContent': 'space-between',
                          'marginBottom': '2px'}),
                html.P(r['grc_location'], style={
                    'fontSize': '11px', 'color': C['muted'],
                    'margin': '0 0 4px 0', 'fontStyle': 'italic',
                }),
                html.Div(style={
                    'height': '1px', 'background': C['border'], 'marginBottom': '8px',
                }),
            ]))
        return html.Div(items, style={'maxHeight': '260px', 'overflowY': 'auto'})

    # ── RESOLUTION TIME ───────────────────────────────────────────────────────
    @app.callback(
        Output('g-resolution-time', 'figure'),
        Input('grc-district-filter', 'value'),
        Input('grc-sector-filter',   'value'),
        Input('grc-cell-filter',     'value'),
    )
    def resolution_time(district, sector, cell):
        df = get_df(district, sector, cell)
        if df.empty:
            return go.Figure()

        counts = df['resolution_cat'].value_counts()
        color_map = {
            'Within 1 day':  C['success'],
            '1 week':        C['p2'],
            '1 month':       C['warning'],
            'Variable':      C['p3'],
            'No complaints': C['muted'],
        }
        colors = [color_map.get(l, C['muted']) for l in counts.index]

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

    # ── TIME VS RATE ──────────────────────────────────────────────────────────
    @app.callback(
        Output('g-time-vs-rate', 'figure'),
        Input('grc-district-filter', 'value'),
        Input('grc-sector-filter',   'value'),
        Input('grc-cell-filter',     'value'),
    )
    def time_vs_rate(district, sector, cell):
        df = get_df(district, sector, cell)
        if df.empty:
            return go.Figure()

        active = df[df['complaints_received'] > 0].copy()
        if active.empty:
            return go.Figure()

        data = active.groupby('resolution_cat').agg(
            avg_resolution=('resolution_rate', 'mean'),
            count=('grc_location', 'count'),
        ).reset_index().sort_values('avg_resolution', ascending=False)

        colors = [C['success'] if v >= 75 else (C['warning'] if v >= 50 else C['danger'])
                  for v in data['avg_resolution']]

        fig = go.Figure(go.Bar(
            x=data['resolution_cat'],
            y=data['avg_resolution'],
            marker_color=colors, marker_line_width=0,
            text=[f'{v:.0f}% (n={int(c)})' for v, c
                  in zip(data['avg_resolution'], data['count'])],
            textposition='outside', textfont=dict(size=12),
        ))
        fig.add_hline(y=75, line_dash='dot', line_color=C['muted'],
                      annotation_text='75% target', annotation_font_size=11)
        fig.update_layout(**BASE_LAYOUT)
        fig.update_xaxes(title='Declared Resolution Time')
        fig.update_yaxes(title='Avg. Actual Resolution Rate (%)',
                         ticksuffix='%', range=[0, 120])
        return fig

    # ── FACILITIES ────────────────────────────────────────────────────────────
    @app.callback(
        Output('g-facilities', 'figure'),
        Input('grc-district-filter', 'value'),
        Input('grc-sector-filter',   'value'),
        Input('grc-cell-filter',     'value'),
    )
    def facilities(district, sector, cell):
        df = get_df(district, sector, cell)
        if df.empty:
            return go.Figure()

        n    = len(df)
        vals = [int(df[col].sum()) for col in FACIL_COLS]
        pcts = [v / n * 100 for v in vals]
        colors = [C['success'] if p >= 60 else (C['warning'] if p >= 40 else C['danger'])
                  for p in pcts]

        # Sort by coverage
        sorted_data = sorted(zip(FACIL_LABELS, vals, pcts, colors),
                             key=lambda x: x[2], reverse=True)
        labels, vals, pcts, colors = zip(*sorted_data)

        fig = go.Figure(go.Bar(
            y=list(labels), x=list(pcts),
            orientation='h',
            marker_color=list(colors), marker_line_width=0,
            text=[f'{v}/{n} ({p:.0f}%)' for v, p in zip(vals, pcts)],
            textposition='outside', textfont=dict(size=12),
        ))
        fig.add_vline(x=60, line_dash='dot', line_color=C['muted'],
                      annotation_text='60% target',
                      annotation_font=dict(size=11, color=C['muted']))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_xaxes(range=[0, 110], ticksuffix='%', title='% of GRCs with facility')
        return fig

    # ── FACILITY vs RESOLUTION ────────────────────────────────────────────────
    @app.callback(
        Output('g-facil-vs-resolution', 'figure'),
        Input('grc-district-filter', 'value'),
        Input('grc-sector-filter',   'value'),
        Input('grc-cell-filter',     'value'),
    )
    def facil_vs_resolution(district, sector, cell):
        df = get_df(district, sector, cell)
        if df.empty:
            return go.Figure()

        active = df[df['complaints_received'] > 0].copy()
        if active.empty:
            return go.Figure()

        # Group by facility score bucket
        active['facil_bucket'] = pd.cut(
            active['facil_score'],
            bins=[-1, 20, 40, 60, 80, 101],
            labels=['0-20%', '21-40%', '41-60%', '61-80%', '81-100%'],
        )
        data = active.groupby('facil_bucket', observed=True).agg(
            avg_res=('resolution_rate', 'mean'),
            count=('grc_location', 'count'),
        ).reset_index()

        colors = [C['success'] if v >= 75 else (C['warning'] if v >= 50 else C['danger'])
                  for v in data['avg_res']]

        fig = go.Figure(go.Bar(
            x=data['facil_bucket'].astype(str),
            y=data['avg_res'],
            marker_color=colors, marker_line_width=0,
            text=[f'{v:.0f}% (n={int(c)})' for v, c
                  in zip(data['avg_res'], data['count'])],
            textposition='outside', textfont=dict(size=12),
        ))
        fig.add_hline(y=75, line_dash='dot', line_color=C['muted'],
                      annotation_text='75% target', annotation_font_size=11)
        fig.update_layout(**BASE_LAYOUT)
        fig.update_xaxes(title='Facility Coverage Score')
        fig.update_yaxes(title='Avg. Resolution Rate (%)',
                         ticksuffix='%', range=[0, 120])
        return fig

    # ── SCORING TABLE ─────────────────────────────────────────────────────────
    @app.callback(
        Output('g-scoring-table', 'children'),
        Input('grc-district-filter', 'value'),
        Input('grc-sector-filter',   'value'),
        Input('grc-cell-filter',     'value'),
    )
    def scoring_table(district, sector, cell):
        df = get_df(district, sector, cell)
        if df.empty:
            return html.Div('No data available.')

        data = df.sort_values('global_score', ascending=False)

        def check_pill(val, yes_val='Yes'):
            ok = str(val) == str(yes_val)
            return html.Span('✓' if ok else '✗', style={
                'fontSize': '14px', 'fontWeight': '900',
                'color': C['success'] if ok else C['danger'],
            })

        rows = []
        for _, r in data.iterrows():
            gc, gb = score_color(float(r['global_score']))
            res_c  = score_color(float(r['resolution_rate']))[0]
            esc_c  = score_color(max(0, 100 - float(r['escalation_rate'])))[0]
            fac_c  = score_color(float(r['facil_score']))[0]
            trn_c  = score_color(float(r['train_score']))[0]

            rows.append(html.Tr([
                # GRC location
                html.Td([
                    html.Div(r['grc_location'], style={
                        'fontWeight': '700', 'fontSize': '12px',
                        'color': C['primary'], 'marginBottom': '2px',
                    }),
                    html.Div(f"{r['district']} • {r['sector']}",
                             style={'fontSize': '10px', 'color': C['muted']}),
                ], style={'padding': '10px 12px', 'minWidth': '180px'}),
                # Complaints
                html.Td(
                    html.Span(
                        f"{int(r['complaints_received'])}",
                        style={'fontSize': '13px', 'fontWeight': '700',
                               'color': C['primary']}
                    ),
                    style={'padding': '10px 8px', 'textAlign': 'center'},
                ),
                # Resolution rate
                html.Td(prog_bar(r['resolution_rate'], res_c),
                        style={'padding': '10px 8px'}),
                # Escalation rate
                html.Td(prog_bar(r['escalation_rate'],
                                 C['danger'] if r['escalation_rate'] > 30
                                 else C['success']),
                        style={'padding': '10px 8px'}),
                # Training
                html.Td(prog_bar(r['train_score'], trn_c),
                        style={'padding': '10px 8px'}),
                # Facilities
                html.Td(prog_bar(r['facil_score'], fac_c),
                        style={'padding': '10px 8px'}),
                # Logbook
                html.Td(check_pill(r['has_logbook'], 'Yes'),
                        style={'padding': '10px 8px', 'textAlign': 'center'}),
                # Pending
                html.Td(
                    html.Span(
                        str(int(r['complaints_pending'])),
                        style={
                            'fontSize': '13px', 'fontWeight': '800',
                            'color': C['danger'] if r['complaints_pending'] > 5
                                     else (C['warning'] if r['complaints_pending'] > 0
                                           else C['success']),
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

        headers = ['GRC Location', 'Complaints', 'Resolution (40%)',
                   'Escalation Rate', 'Training (20%)',
                   'Facilities (20%)', 'Logbook', 'Pending', 'Global Score']

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