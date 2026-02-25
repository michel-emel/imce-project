"""
IMCE Dashboard — Workers Page (Deep Analysis)
Filters: Site → Role → Gender
Sections: KPIs, Profile, Rights, Safety, Training, Payment, GRM, Risk Scoring
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
# SITE CATEGORY MAPPING (per recommendation)
# ─────────────────────────────────────────────────────────────────────────────

SITE_CATEGORY = {
    'Nyagatovu':                    'Informal Settlement',
    'Gatenga':                      'Informal Settlement',
    'Kinyinya':                     'Informal Settlement',
    'Rugunga':                      'Wetland / Flood Risk',
    'Rwandex':                      'Wetland / Flood Risk',
    'Gikondo':                      'Wetland / Flood Risk',
    'Gasabo-kicyiru':               'Wetland / Flood Risk',
    'Nyarugenge- Gasabo- Muhima':   'Wetland / Flood Risk',
    'Rwampala':                     'Wetland / Flood Risk',
    'Cyuve':                        'Secondary City',
    'Muhanga':                      'Secondary City',
    'Huye':                         'Secondary City',
    'Kigarama':                     'Secondary City',
    'Nguga':                        'Secondary City',
    'Outlet roundabout':            'Secondary City',
    'Gacamahembe':                  'Secondary City',
}

CAT_COLORS = {
    'Informal Settlement':  C['p4'],
    'Wetland / Flood Risk': C['p2'],
    'Secondary City':       C['p1'],
}

# ─────────────────────────────────────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────────────────────────────────────

def load_workers():
    import os
    paths = [
        'workers_clean.csv',
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'workers_clean.csv'),
    ]
    df = pd.DataFrame()
    for p in paths:
        if os.path.exists(p):
            df = pd.read_csv(p)
            break
    if df.empty:
        return df

    df['site_name'] = df['site_name'].str.strip()

    pay_map = {
        'Monthly + 5 days':                  'Monthly',
        'Monthly + 3 days':                  'Monthly',
        'Mixed (some monthly, some bi-weekly)': 'Bi-weekly',
    }
    df['payment_frequency'] = df['payment_frequency'].replace(pay_map)

    # Site category
    df['site_category'] = df['site_name'].map(SITE_CATEGORY).fillna('Other')

    # Vulnerability score (number of rights deficits)
    vuln_cols = ['signed_contract', 'code_of_conduct', 'health_insurance',
                 'ppe_received', 'payment_on_time']
    df['vuln_score'] = sum(df[c].eq('No').astype(int) for c in vuln_cols)

    # Training score (0-5)
    train_cols = ['train_health_safety', 'train_gbv', 'train_hiv',
                  'train_road_safety', 'train_environment']
    df['train_score'] = df[train_cols].sum(axis=1)

    return df


WORKERS = load_workers()


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


def get_df(site, role, gender):
    df = WORKERS.copy()
    if df.empty:
        return df
    if site and site != 'ALL':
        df = df[df['site_name'] == site]
    if role and role != 'ALL':
        df = df[df['role'] == role]
    if gender and gender != 'ALL':
        df = df[df['gender'] == gender]
    return df


# ─────────────────────────────────────────────────────────────────────────────
# FILTER BAR
# ─────────────────────────────────────────────────────────────────────────────

def filter_bar():
    sites = sorted(WORKERS['site_name'].unique().tolist()) if not WORKERS.empty else []
    dd = {'width': '200px', 'fontFamily': 'Nunito, sans-serif', 'fontSize': '13px'}
    lb = {
        'fontSize': '11px', 'fontWeight': '700', 'textTransform': 'uppercase',
        'letterSpacing': '1px', 'color': C['muted'], 'marginBottom': '4px',
        'display': 'block',
    }
    return html.Div([
        html.Div([
            html.Label('Site', style=lb),
            dcc.Dropdown(
                id='workers-site-filter',
                options=[{'label': 'All Sites', 'value': 'ALL'}] +
                        [{'label': s, 'value': s} for s in sites],
                value='ALL', clearable=False, style=dd,
            ),
        ]),
        html.Div([
            html.Label('Role', style=lb),
            dcc.Dropdown(
                id='workers-role-filter',
                options=[{'label': 'All Roles', 'value': 'ALL'}],
                value='ALL', clearable=False, style=dd,
            ),
        ]),
        html.Div([
            html.Label('Gender', style=lb),
            dcc.Dropdown(
                id='workers-gender-filter',
                options=[{'label': 'All Genders', 'value': 'ALL'}],
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
    if WORKERS.empty:
        return html.Div('workers_clean.csv not found.',
                        style={'padding': '40px 40px 40px 260px'})

    n           = len(WORKERS)
    acc_rate    = WORKERS['accident_occurred'].eq('Yes').mean() * 100
    contr_rate  = WORKERS['signed_contract'].eq('Yes').mean() * 100

    if contr_rate >= 80 and acc_rate <= 15:
        sc, st, sb = C['success'], '● ON TRACK', '#E8F5E9'
    elif contr_rate >= 50 or acc_rate <= 30:
        sc, st, sb = C['warning'], '● ATTENTION REQUIRED', '#FFF3E0'
    else:
        sc, st, sb = C['danger'], '● CRITICAL', '#FFEBEE'

    return html.Div([

        # PAGE HEADER
        html.Div([
            html.Div([
                html.H2('Workers', style={
                    'margin': '0 0 4px 0', 'fontWeight': '900',
                    'fontSize': '26px', 'color': C['primary'],
                }),
                html.P(
                    f'{n} workers surveyed across {WORKERS["site_name"].nunique()} sites — IMCE Project Rwanda',
                    style={'margin': '0', 'color': C['muted'], 'fontSize': '14px'},
                ),
            ]),
            html.Div([
                # Category legend
                html.Div([
                    html.Div([
                        html.Span(style={
                            'width': '10px', 'height': '10px', 'borderRadius': '50%',
                            'background': color, 'display': 'inline-block', 'marginRight': '5px',
                        }),
                        html.Span(cat, style={'fontSize': '11px', 'color': C['muted'],
                                              'fontWeight': '600', 'marginRight': '12px'}),
                    ], style={'display': 'inline-flex', 'alignItems': 'center'})
                    for cat, color in CAT_COLORS.items()
                ], style={'marginBottom': '8px'}),
                html.Span(st, style={
                    'background': sb, 'color': sc, 'padding': '6px 16px',
                    'borderRadius': '20px', 'fontSize': '13px', 'fontWeight': '700',
                    'border': f'1px solid {sc}',
                }),
            ], style={'textAlign': 'right'}),
        ], style={
            'display': 'flex', 'justifyContent': 'space-between',
            'alignItems': 'center', 'marginBottom': '24px',
        }),

        # FILTERS
        filter_bar(),

        # SECTION 1 — KPIs
        dbc.Row([
            dbc.Col(html.Div(id='w-kpi-total'),    md=2),
            dbc.Col(html.Div(id='w-kpi-contract'), md=2),
            dbc.Col(html.Div(id='w-kpi-insurance'),md=2),
            dbc.Col(html.Div(id='w-kpi-ppe'),      md=2),
            dbc.Col(html.Div(id='w-kpi-accident'), md=2),
            dbc.Col(html.Div(id='w-kpi-vuln'),     md=2),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 2 — Workforce profile
        dbc.Row([
            dbc.Col([card([
                section_title('Workers by Site & Category',
                              'Distribution across informal settlements, wetlands and secondary cities'),
                dcc.Graph(id='w-site-category',
                          config={'displayModeBar': False}, style={'height': '300px'}),
            ])], md=5),
            dbc.Col([card([
                section_title('Role Distribution',
                              'Types of roles and their gender breakdown'),
                dcc.Graph(id='w-role-gender',
                          config={'displayModeBar': False}, style={'height': '300px'}),
            ])], md=4),
            dbc.Col([card([
                section_title('Age Distribution by Gender',
                              'Age profile of the workforce'),
                dcc.Graph(id='w-age-gender',
                          config={'displayModeBar': False}, style={'height': '300px'}),
            ])], md=3),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 3 — Fundamental rights
        dbc.Row([
            dbc.Col([card([
                section_title('Labour Rights Compliance',
                              'Core rights indicators — contract, code of conduct, insurance, PPE, payment'),
                dcc.Graph(id='w-rights-overall',
                          config={'displayModeBar': False}, style={'height': '280px'}),
            ])], md=5),
            dbc.Col([card([
                section_title('Rights Compliance by Role',
                              'Which roles have the lowest contract and rights coverage?'),
                dcc.Graph(id='w-rights-by-role',
                          config={'displayModeBar': False}, style={'height': '280px'}),
            ])], md=7),
        ], className='g-3', style={'marginBottom': '24px'}),

        dbc.Row([
            dbc.Col([card([
                section_title('Rights Compliance by Gender',
                              'Are there disparities between male and female workers?'),
                dcc.Graph(id='w-rights-gender',
                          config={'displayModeBar': False}, style={'height': '260px'}),
            ])], md=6),
            dbc.Col([card([
                section_title('Cumulative Vulnerability Profile',
                              'How many workers cumulate multiple rights deficits?'),
                dcc.Graph(id='w-vuln-profile',
                          config={'displayModeBar': False}, style={'height': '260px'}),
            ])], md=6),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 4 — Safety & accidents
        dbc.Row([
            dbc.Col([card([
                section_title('Accident Rate by Site',
                              'Sites with the highest accident rates require immediate attention'),
                dcc.Graph(id='w-accident-site',
                          config={'displayModeBar': False}, style={'height': '300px'}),
            ])], md=6),
            dbc.Col([card([
                section_title('Accident Types',
                              'Nature of accidents reported by workers on project sites'),
                dcc.Graph(id='w-accident-types',
                          config={'displayModeBar': False}, style={'height': '300px'}),
            ])], md=3),
            dbc.Col([card([
                section_title('Accidents by Role',
                              'Which roles are most exposed to accidents?'),
                dcc.Graph(id='w-accident-role',
                          config={'displayModeBar': False}, style={'height': '300px'}),
            ])], md=3),
        ], className='g-3', style={'marginBottom': '24px'}),

        dbc.Row([
            dbc.Col([card([
                section_title('Accident vs Training — Key Insight',
                              'Do workers with more training have fewer accidents?'),
                dcc.Graph(id='w-accident-training',
                          config={'displayModeBar': False}, style={'height': '280px'}),
            ])], md=7),
            dbc.Col([card([
                section_title('PPE Availability vs Accidents',
                              'PPE status among workers who experienced accidents'),
                dcc.Graph(id='w-accident-ppe',
                          config={'displayModeBar': False}, style={'height': '280px'}),
            ])], md=5),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 5 — Training
        dbc.Row([
            dbc.Col([card([
                section_title('Training Coverage by Type',
                              'Percentage of workers who received each type of training'),
                dcc.Graph(id='w-training-types',
                          config={'displayModeBar': False}, style={'height': '280px'}),
            ])], md=6),
            dbc.Col([card([
                section_title('Training Score by Site',
                              'Average number of trainings received per site (max 5)'),
                dcc.Graph(id='w-training-site',
                          config={'displayModeBar': False}, style={'height': '280px'}),
            ])], md=6),
        ], className='g-3', style={'marginBottom': '24px'}),

        dbc.Row([
            dbc.Col([card([
                section_title('Workers with Zero Training',
                              '21 workers received no training at all — who are they?'),
                html.Div(id='w-zero-training-table'),
            ])], md=12),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 6 — Payment
        dbc.Row([
            dbc.Col([card([
                section_title('Payment Frequency Distribution',
                              'How are workers paid across project sites?'),
                dcc.Graph(id='w-payment-freq',
                          config={'displayModeBar': False}, style={'height': '260px'}),
            ])], md=4),
            dbc.Col([card([
                section_title('Payment Frequency by Site',
                              'Are payment practices consistent across sites?'),
                dcc.Graph(id='w-payment-site',
                          config={'displayModeBar': False}, style={'height': '260px'}),
            ])], md=8),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 7 — GRM
        dbc.Row([
            dbc.Col([card([
                section_title('Grievance Channels Known to Workers',
                              'How do workers report complaints and concerns?'),
                dcc.Graph(id='w-grievance-channel',
                          config={'displayModeBar': False}, style={'height': '280px'}),
            ])], md=6),
            dbc.Col([card([
                section_title('GRM Awareness by Contract Status',
                              'Do workers without contracts know less about grievance mechanisms?'),
                dcc.Graph(id='w-grm-contract',
                          config={'displayModeBar': False}, style={'height': '280px'}),
            ])], md=6),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 8 — Site risk scoring
        dbc.Row([
            dbc.Col([card([
                section_title('Site Risk Scoring Dashboard',
                              'Composite E&S risk score per site — contract, training, safety, PPE. Red = urgent action needed.'),
                html.Div(id='w-site-risk'),
            ])], md=8),
            dbc.Col([card([
                section_title('Risk Summary',
                              'Key vulnerability indicators across all workers'),
                html.Div(id='w-risk-summary'),
            ])], md=4),
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

    # ── CASCADE: role options ─────────────────────────────────────────────────
    @app.callback(
        Output('workers-role-filter', 'options'),
        Output('workers-role-filter', 'value'),
        Input('workers-site-filter', 'value'),
    )
    def update_role_options(site):
        df = WORKERS.copy()
        if site and site != 'ALL':
            df = df[df['site_name'] == site]
        roles = sorted(df['role'].dropna().unique().tolist())
        options = [{'label': 'All Roles', 'value': 'ALL'}] + \
                  [{'label': r, 'value': r} for r in roles]
        return options, 'ALL'

    # ── CASCADE: gender options ───────────────────────────────────────────────
    @app.callback(
        Output('workers-gender-filter', 'options'),
        Output('workers-gender-filter', 'value'),
        Input('workers-site-filter', 'value'),
        Input('workers-role-filter', 'value'),
    )
    def update_gender_options(site, role):
        df = WORKERS.copy()
        if site and site != 'ALL':
            df = df[df['site_name'] == site]
        if role and role != 'ALL':
            df = df[df['role'] == role]
        genders = sorted(df['gender'].dropna().unique().tolist())
        options = [{'label': 'All Genders', 'value': 'ALL'}] + \
                  [{'label': g, 'value': g} for g in genders]
        return options, 'ALL'

    # ── KPIs ─────────────────────────────────────────────────────────────────
    @app.callback(
        Output('w-kpi-total',     'children'),
        Output('w-kpi-contract',  'children'),
        Output('w-kpi-insurance', 'children'),
        Output('w-kpi-ppe',       'children'),
        Output('w-kpi-accident',  'children'),
        Output('w-kpi-vuln',      'children'),
        Input('workers-site-filter',   'value'),
        Input('workers-role-filter',   'value'),
        Input('workers-gender-filter', 'value'),
    )
    def update_kpis(site, role, gender):
        df = get_df(site, role, gender)
        if df.empty:
            return [html.Div('—')] * 6
        n         = len(df)
        contr_pct = df['signed_contract'].eq('Yes').mean() * 100
        ins_pct   = df['health_insurance'].eq('Yes').mean() * 100
        ppe_pct   = df['ppe_received'].eq('Yes').mean() * 100
        acc_pct   = df['accident_occurred'].eq('Yes').mean() * 100
        vuln_3    = df['vuln_score'].ge(3).sum()

        cc = C['warning'] if contr_pct < 80 else C['success']
        ic = C['success'] if ins_pct >= 80 else C['warning']
        pc = C['success'] if ppe_pct >= 95 else C['warning']
        ac = C['danger']  if acc_pct > 25 else (C['warning'] if acc_pct > 10 else C['success'])
        vc = C['danger']  if vuln_3 > 5 else (C['warning'] if vuln_3 > 0 else C['success'])

        return (
            kpi('Workers Surveyed',   str(n),
                f'{df["site_name"].nunique()} sites', C['accent']),
            kpi('Contract Coverage',  f'{contr_pct:.0f}%',
                f'{df["signed_contract"].eq("Yes").sum()} with signed contract', cc),
            kpi('Health Insurance',   f'{ins_pct:.0f}%',
                f'{df["health_insurance"].eq("Yes").sum()} covered', ic),
            kpi('PPE Provided',       f'{ppe_pct:.0f}%',
                f'{df["ppe_received"].eq("Yes").sum()} received PPE', pc),
            kpi('Accident Rate',      f'{acc_pct:.0f}%',
                f'{df["accident_occurred"].eq("Yes").sum()} workers affected', ac),
            kpi('High-Risk Workers',  str(vuln_3),
                '3+ rights deficits cumulated', vc),
        )

    # ── SITE CATEGORY ─────────────────────────────────────────────────────────
    @app.callback(
        Output('w-site-category', 'figure'),
        Input('workers-site-filter',   'value'),
        Input('workers-role-filter',   'value'),
        Input('workers-gender-filter', 'value'),
    )
    def site_category(site, role, gender):
        df = get_df(site, role, gender)
        if df.empty:
            return go.Figure()

        data = df.groupby(['site_name', 'site_category']).size().reset_index(name='count')
        data = data.sort_values(['site_category', 'count'], ascending=[True, False])

        fig = go.Figure()
        for cat, color in CAT_COLORS.items():
            sub = data[data['site_category'] == cat]
            if sub.empty:
                continue
            fig.add_trace(go.Bar(
                name=cat,
                x=sub['site_name'], y=sub['count'],
                marker_color=color, marker_line_width=0,
                text=sub['count'], textposition='outside',
                textfont=dict(size=11),
            ))
        fig.update_layout(**BASE_LAYOUT, barmode='stack')
        fig.update_xaxes(tickangle=-30)
        fig.update_yaxes(title='Number of Workers')
        return fig

    # ── ROLE / GENDER ─────────────────────────────────────────────────────────
    @app.callback(
        Output('w-role-gender', 'figure'),
        Input('workers-site-filter',   'value'),
        Input('workers-role-filter',   'value'),
        Input('workers-gender-filter', 'value'),
    )
    def role_gender(site, role, gender):
        df = get_df(site, role, gender)
        if df.empty:
            return go.Figure()

        grp = df.groupby(['role', 'gender']).size().reset_index(name='count')
        roles = df.groupby('role').size().sort_values(ascending=False).index.tolist()

        fig = go.Figure()
        for g, color in [('Male', C['accent']), ('Female', C['secondary'])]:
            vals = [grp.query(f'role=="{r}" and gender=="{g}"')['count'].sum()
                    for r in roles]
            fig.add_trace(go.Bar(
                name=g, y=roles, x=vals, orientation='h',
                marker_color=color, marker_line_width=0,
                text=[v if v > 0 else '' for v in vals],
                textposition='inside',
                textfont=dict(color='white', size=11),
            ))
        fig.update_layout(**BASE_LAYOUT, barmode='stack')
        fig.update_xaxes(title='Number of Workers')
        return fig

    # ── AGE / GENDER ──────────────────────────────────────────────────────────
    @app.callback(
        Output('w-age-gender', 'figure'),
        Input('workers-site-filter',   'value'),
        Input('workers-role-filter',   'value'),
        Input('workers-gender-filter', 'value'),
    )
    def age_gender(site, role, gender):
        df = get_df(site, role, gender)
        if df.empty:
            return go.Figure()

        bins   = [18, 25, 30, 35, 40, 50, 70]
        labels = ['18-24', '25-29', '30-34', '35-39', '40-49', '50+']
        df['age_group'] = pd.cut(df['age'], bins=bins, labels=labels, right=False)

        fig = go.Figure()
        for g, color in [('Male', C['accent']), ('Female', C['secondary'])]:
            sub    = df[df['gender'] == g]
            counts = sub['age_group'].value_counts().reindex(labels, fill_value=0)
            fig.add_trace(go.Bar(
                name=g, x=labels, y=counts.values,
                marker_color=color, marker_line_width=0,
                text=counts.values, textposition='outside',
                textfont=dict(size=11),
            ))
        fig.update_layout(**BASE_LAYOUT, barmode='group')
        fig.update_xaxes(title='Age Group')
        fig.update_yaxes(title='Number of Workers')
        return fig

    # ── RIGHTS OVERALL ────────────────────────────────────────────────────────
    @app.callback(
        Output('w-rights-overall', 'figure'),
        Input('workers-site-filter',   'value'),
        Input('workers-role-filter',   'value'),
        Input('workers-gender-filter', 'value'),
    )
    def rights_overall(site, role, gender):
        df = get_df(site, role, gender)
        if df.empty:
            return go.Figure()
        n = len(df)
        rights = {
            'Signed Contract':  df['signed_contract'].eq('Yes').sum(),
            'Code of Conduct':  df['code_of_conduct'].eq('Yes').sum(),
            'Health Insurance': df['health_insurance'].eq('Yes').sum(),
            'PPE Provided':     df['ppe_received'].eq('Yes').sum(),
            'Paid on Time':     df['payment_on_time'].eq('Yes').sum(),
        }
        labels = list(rights.keys())
        pcts   = [v / n * 100 for v in rights.values()]
        colors = [C['success'] if p >= 80 else (C['warning'] if p >= 50 else C['danger'])
                  for p in pcts]

        fig = go.Figure(go.Bar(
            y=labels, x=pcts, orientation='h',
            marker_color=colors, marker_line_width=0,
            text=[f'{p:.0f}% ({v}/{n})' for p, v in zip(pcts, rights.values())],
            textposition='outside', textfont=dict(size=12),
        ))
        fig.add_vline(x=80, line_dash='dot', line_color=C['muted'],
                      annotation_text='80% target',
                      annotation_font=dict(size=11, color=C['muted']))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_xaxes(range=[0, 120], ticksuffix='%', title='Compliance Rate')
        return fig

    # ── RIGHTS BY ROLE ────────────────────────────────────────────────────────
    @app.callback(
        Output('w-rights-by-role', 'figure'),
        Input('workers-site-filter',   'value'),
        Input('workers-role-filter',   'value'),
        Input('workers-gender-filter', 'value'),
    )
    def rights_by_role(site, role, gender):
        df = get_df(site, role, gender)
        if df.empty:
            return go.Figure()

        roles = df.groupby('role').size().sort_values(ascending=False).index.tolist()
        rights_cols = {
            'signed_contract': 'Contract',
            'code_of_conduct': 'Code of Conduct',
            'health_insurance': 'Insurance',
        }
        fig = go.Figure()
        for col, label in rights_cols.items():
            vals = [df[df['role'] == r][col].eq('Yes').mean() * 100 for r in roles]
            fig.add_trace(go.Bar(
                name=label, x=roles, y=vals,
                marker_line_width=0,
                text=[f'{v:.0f}%' for v in vals],
                textposition='outside', textfont=dict(size=11),
            ))
        fig.update_layout(**BASE_LAYOUT, barmode='group')
        fig.update_xaxes(tickangle=-20)
        fig.update_yaxes(title='Compliance Rate (%)', ticksuffix='%', range=[0, 125])
        return fig

    # ── RIGHTS BY GENDER ──────────────────────────────────────────────────────
    @app.callback(
        Output('w-rights-gender', 'figure'),
        Input('workers-site-filter',   'value'),
        Input('workers-role-filter',   'value'),
        Input('workers-gender-filter', 'value'),
    )
    def rights_by_gender(site, role, gender):
        df = get_df(site, role, gender)
        if df.empty:
            return go.Figure()

        rights = {
            'Contract':  'signed_contract',
            'Code of Conduct': 'code_of_conduct',
            'Insurance': 'health_insurance',
            'PPE':       'ppe_received',
            'On-time Pay': 'payment_on_time',
        }
        fig = go.Figure()
        for g, color in [('Male', C['accent']), ('Female', C['secondary'])]:
            sub  = df[df['gender'] == g]
            vals = [sub[col].eq('Yes').mean() * 100 if len(sub) > 0 else 0
                    for col in rights.values()]
            fig.add_trace(go.Bar(
                name=g, x=list(rights.keys()), y=vals,
                marker_color=color, marker_line_width=0,
                text=[f'{v:.0f}%' for v in vals],
                textposition='outside', textfont=dict(size=11),
            ))
        fig.update_layout(**BASE_LAYOUT, barmode='group')
        fig.update_yaxes(title='Compliance Rate (%)', ticksuffix='%', range=[0, 125])
        return fig

    # ── VULNERABILITY PROFILE ─────────────────────────────────────────────────
    @app.callback(
        Output('w-vuln-profile', 'figure'),
        Input('workers-site-filter',   'value'),
        Input('workers-role-filter',   'value'),
        Input('workers-gender-filter', 'value'),
    )
    def vuln_profile(site, role, gender):
        df = get_df(site, role, gender)
        if df.empty:
            return go.Figure()

        counts = df['vuln_score'].value_counts().sort_index()
        labels_map = {
            0: 'No deficit',
            1: '1 deficit',
            2: '2 deficits',
            3: '3 deficits',
            4: '4 deficits',
            5: '5 deficits',
        }
        colors_map = {0: C['success'], 1: C['p2'], 2: C['p3'],
                      3: C['warning'],  4: C['danger'], 5: '#7B0000'}

        fig = go.Figure(go.Bar(
            x=[labels_map.get(i, str(i)) for i in counts.index],
            y=counts.values,
            marker_color=[colors_map.get(i, C['muted']) for i in counts.index],
            marker_line_width=0,
            text=counts.values, textposition='outside', textfont=dict(size=13),
        ))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_yaxes(title='Number of Workers')
        return fig

    # ── ACCIDENT RATE BY SITE ─────────────────────────────────────────────────
    @app.callback(
        Output('w-accident-site', 'figure'),
        Input('workers-site-filter',   'value'),
        Input('workers-role-filter',   'value'),
        Input('workers-gender-filter', 'value'),
    )
    def accident_site(site, role, gender):
        df = get_df(site, role, gender)
        if df.empty:
            return go.Figure()

        data = df.groupby(['site_name', 'site_category']).apply(
            lambda x: pd.Series({
                'acc_rate': x['accident_occurred'].eq('Yes').mean() * 100,
                'count': len(x),
                'acc_count': x['accident_occurred'].eq('Yes').sum(),
            })
        ).reset_index().sort_values('acc_rate', ascending=True)

        cat_color = [CAT_COLORS.get(c, C['muted']) for c in data['site_category']]

        fig = go.Figure(go.Bar(
            y=data['site_name'], x=data['acc_rate'],
            orientation='h',
            marker_color=cat_color, marker_line_width=0,
            text=[f'{r:.0f}% ({int(ac)}/{int(n)})' for r, ac, n
                  in zip(data['acc_rate'], data['acc_count'], data['count'])],
            textposition='outside', textfont=dict(size=11),
            customdata=data['site_category'],
            hovertemplate='%{y}<br>Accident Rate: %{x:.0f}%<br>Category: %{customdata}<extra></extra>',
        ))
        fig.add_vline(x=20, line_dash='dot', line_color=C['danger'],
                      annotation_text='20% threshold',
                      annotation_font=dict(size=11, color=C['danger']))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_xaxes(range=[0, 130], ticksuffix='%', title='Accident Rate')
        return fig

    # ── ACCIDENT TYPES ────────────────────────────────────────────────────────
    @app.callback(
        Output('w-accident-types', 'figure'),
        Input('workers-site-filter',   'value'),
        Input('workers-role-filter',   'value'),
        Input('workers-gender-filter', 'value'),
    )
    def accident_types(site, role, gender):
        df = get_df(site, role, gender)
        if df.empty:
            return go.Figure()

        acc_map = {
            'acc_wound':     'Wound',
            'acc_stones':    'Falling Stones',
            'acc_equipment': 'Equipment',
            'acc_flooding':  'Flooding',
            'acc_transport': 'Transport',
            'acc_other':     'Other',
        }
        counts = {lbl: df[col].sum() for col, lbl in acc_map.items()}
        counts = {k: v for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True) if v > 0}

        fig = go.Figure(go.Pie(
            labels=list(counts.keys()), values=list(counts.values()),
            hole=0.5,
            marker_colors=PALETTE[:len(counts)],
            textinfo='label+value',
            textfont=dict(size=11, family='Nunito, sans-serif'),
            showlegend=False,
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Nunito, sans-serif', size=13,
                      color=C['primary']),
            margin=dict(l=10, r=10, t=10, b=10),
            hoverlabel=dict(bgcolor=C['primary'], bordercolor=C['border'],
                            font=dict(family='Nunito, sans-serif', size=13,
                                      color='#FFFFFF')),
        )
        return fig

    # ── ACCIDENT BY ROLE ──────────────────────────────────────────────────────
    @app.callback(
        Output('w-accident-role', 'figure'),
        Input('workers-site-filter',   'value'),
        Input('workers-role-filter',   'value'),
        Input('workers-gender-filter', 'value'),
    )
    def accident_role(site, role, gender):
        df = get_df(site, role, gender)
        if df.empty:
            return go.Figure()

        data = df.groupby('role').apply(
            lambda x: pd.Series({
                'acc_rate': x['accident_occurred'].eq('Yes').mean() * 100,
                'count': len(x),
            })
        ).reset_index().sort_values('acc_rate', ascending=True)

        colors = [C['danger'] if r > 40 else (C['warning'] if r > 20 else C['success'])
                  for r in data['acc_rate']]

        fig = go.Figure(go.Bar(
            y=data['role'], x=data['acc_rate'],
            orientation='h',
            marker_color=colors, marker_line_width=0,
            text=[f'{r:.0f}%' for r in data['acc_rate']],
            textposition='outside', textfont=dict(size=11),
        ))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_xaxes(range=[0, 130], ticksuffix='%', title='Accident Rate')
        return fig

    # ── ACCIDENT vs TRAINING ──────────────────────────────────────────────────
    @app.callback(
        Output('w-accident-training', 'figure'),
        Input('workers-site-filter',   'value'),
        Input('workers-role-filter',   'value'),
        Input('workers-gender-filter', 'value'),
    )
    def accident_training(site, role, gender):
        df = get_df(site, role, gender)
        if df.empty:
            return go.Figure()

        data = df.groupby('training_count').apply(
            lambda x: pd.Series({
                'acc_rate':  x['accident_occurred'].eq('Yes').mean() * 100,
                'count':     len(x),
                'acc_count': x['accident_occurred'].eq('Yes').sum(),
            })
        ).reset_index()

        colors = [C['danger'] if r > 40 else (C['warning'] if r > 20 else C['success'])
                  for r in data['acc_rate']]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Number of Workers',
            x=data['training_count'].astype(str), y=data['count'],
            marker_color=C['accent'], marker_line_width=0,
            text=data['count'], textposition='outside',
            yaxis='y', offsetgroup=0,
        ))
        fig.add_trace(go.Scatter(
            name='Accident Rate',
            x=data['training_count'].astype(str), y=data['acc_rate'],
            mode='lines+markers+text',
            line=dict(color=C['danger'], width=2.5),
            marker=dict(color=colors, size=12, line=dict(color='white', width=2)),
            text=[f'{r:.0f}%' for r in data['acc_rate']],
            textposition='top center',
            textfont=dict(size=12, color=C['primary']),
            yaxis='y2',
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Nunito, sans-serif', color=C['primary'], size=13),
            margin=dict(l=10, r=10, t=35, b=10),
            legend=dict(orientation='h', y=1.12, x=0, font=dict(size=12)),
            barmode='group',
            yaxis2=dict(
                title='Accident Rate (%)', overlaying='y', side='right',
                range=[0, 100], ticksuffix='%',
                gridcolor='rgba(0,0,0,0)', linecolor=C['border'],
                tickfont=dict(size=12),
            ),
            hoverlabel=dict(bgcolor=C['primary'], bordercolor=C['border'],
                            font=dict(family='Nunito, sans-serif', size=13,
                                      color='#FFFFFF')),
        )
        fig.update_xaxes(title='Number of Trainings Received',
                         tickfont=dict(size=12), gridcolor=C['border'],
                         linecolor=C['border'])
        fig.update_yaxes(title='Number of Workers', gridcolor=C['border'],
                         linecolor=C['border'], tickfont=dict(size=12))
        return fig

    # ── ACCIDENT vs PPE ───────────────────────────────────────────────────────
    @app.callback(
        Output('w-accident-ppe', 'figure'),
        Input('workers-site-filter',   'value'),
        Input('workers-role-filter',   'value'),
        Input('workers-gender-filter', 'value'),
    )
    def accident_ppe(site, role, gender):
        df = get_df(site, role, gender)
        if df.empty:
            return go.Figure()

        cats = {
            'Accident + PPE':       ((df['accident_occurred'] == 'Yes') & (df['ppe_received'] == 'Yes')).sum(),
            'Accident + No PPE':    ((df['accident_occurred'] == 'Yes') & (df['ppe_received'] == 'No')).sum(),
            'No Accident + PPE':    ((df['accident_occurred'] == 'No')  & (df['ppe_received'] == 'Yes')).sum(),
            'No Accident + No PPE': ((df['accident_occurred'] == 'No')  & (df['ppe_received'] == 'No')).sum(),
        }
        colors_list = [C['warning'], C['danger'], C['success'], C['p3']]

        fig = go.Figure(go.Bar(
            x=list(cats.keys()), y=list(cats.values()),
            marker_color=colors_list, marker_line_width=0,
            text=list(cats.values()), textposition='outside', textfont=dict(size=13),
        ))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_xaxes(tickangle=-15)
        fig.update_yaxes(title='Number of Workers')
        return fig

    # ── TRAINING TYPES ────────────────────────────────────────────────────────
    @app.callback(
        Output('w-training-types', 'figure'),
        Input('workers-site-filter',   'value'),
        Input('workers-role-filter',   'value'),
        Input('workers-gender-filter', 'value'),
    )
    def training_types(site, role, gender):
        df = get_df(site, role, gender)
        if df.empty:
            return go.Figure()
        n = len(df)
        trainings = {
            'Health & Safety': df['train_health_safety'].sum(),
            'GBV/SEA':         df['train_gbv'].sum(),
            'HIV/AIDS':        df['train_hiv'].sum(),
            'Road Safety':     df['train_road_safety'].sum(),
            'Environment':     df['train_environment'].sum(),
        }
        pcts   = [v / n * 100 for v in trainings.values()]
        colors = [C['success'] if p >= 60 else (C['warning'] if p >= 40 else C['danger'])
                  for p in pcts]

        fig = go.Figure(go.Bar(
            x=list(trainings.keys()), y=pcts,
            marker_color=colors, marker_line_width=0,
            text=[f'{p:.0f}% ({v})' for p, v in zip(pcts, trainings.values())],
            textposition='outside', textfont=dict(size=12),
        ))
        fig.add_hline(y=60, line_dash='dot', line_color=C['muted'],
                      annotation_text='60% target', annotation_font_size=11)
        fig.update_layout(**BASE_LAYOUT)
        fig.update_yaxes(title='% of Workers Trained', ticksuffix='%', range=[0, 90])
        return fig

    # ── TRAINING BY SITE ──────────────────────────────────────────────────────
    @app.callback(
        Output('w-training-site', 'figure'),
        Input('workers-site-filter',   'value'),
        Input('workers-role-filter',   'value'),
        Input('workers-gender-filter', 'value'),
    )
    def training_site(site, role, gender):
        df = get_df(site, role, gender)
        if df.empty:
            return go.Figure()

        data = df.groupby(['site_name', 'site_category']).apply(
            lambda x: pd.Series({
                'avg_train': x['train_score'].mean(),
                'no_train':  x['training_count'].eq(0).sum(),
                'count':     len(x),
            })
        ).reset_index().sort_values('avg_train', ascending=True)

        cat_color = [CAT_COLORS.get(c, C['muted']) for c in data['site_category']]

        fig = go.Figure(go.Bar(
            y=data['site_name'], x=data['avg_train'],
            orientation='h',
            marker_color=cat_color, marker_line_width=0,
            text=[f'{v:.1f} (no training: {int(nt)}/{int(n)})'
                  for v, nt, n in zip(data['avg_train'], data['no_train'], data['count'])],
            textposition='outside', textfont=dict(size=11),
        ))
        fig.add_vline(x=2.5, line_dash='dot', line_color=C['muted'],
                      annotation_text='target ≥ 2.5',
                      annotation_font=dict(size=11, color=C['muted']))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_xaxes(range=[0, 6.5], title='Avg. Training Score (out of 5)')
        return fig

    # ── ZERO TRAINING TABLE ───────────────────────────────────────────────────
    @app.callback(
        Output('w-zero-training-table', 'children'),
        Input('workers-site-filter',   'value'),
        Input('workers-role-filter',   'value'),
        Input('workers-gender-filter', 'value'),
    )
    def zero_training_table(site, role, gender):
        df   = get_df(site, role, gender)
        zero = df[df['training_count'] == 0].copy()

        if zero.empty:
            return html.Div([
                html.Span('✓', style={'fontSize': '28px', 'color': C['success']}),
                html.P('All workers in this selection have received at least one training.',
                       style={'color': C['success'], 'fontWeight': '700',
                              'margin': '8px 0 0 0', 'fontSize': '14px'}),
            ], style={'textAlign': 'center', 'padding': '20px'})

        rows = []
        for _, r in zero.iterrows():
            acc = r.get('accident_occurred', 'No')
            rows.append(html.Tr([
                html.Td(r.get('worker_name', '—'),
                        style={'fontWeight': '700', 'fontSize': '13px', 'padding': '9px 12px'}),
                html.Td(r.get('site_name', '—'),
                        style={'fontSize': '13px', 'padding': '9px 12px'}),
                html.Td(html.Span(
                    r.get('site_category', '—'),
                    style={
                        'background': CAT_COLORS.get(r.get('site_category', ''), C['muted']) + '22',
                        'color': CAT_COLORS.get(r.get('site_category', ''), C['muted']),
                        'padding': '2px 10px', 'borderRadius': '12px',
                        'fontSize': '11px', 'fontWeight': '700',
                    }
                ), style={'padding': '9px 12px'}),
                html.Td(r.get('role', '—'),
                        style={'fontSize': '13px', 'padding': '9px 12px'}),
                html.Td(r.get('gender', '—'),
                        style={'fontSize': '13px', 'padding': '9px 12px'}),
                html.Td(str(int(r.get('age', 0))),
                        style={'fontSize': '13px', 'padding': '9px 12px', 'textAlign': 'center'}),
                html.Td(
                    html.Span(acc, style={
                        'background': '#FFEBEE' if acc == 'Yes' else '#E8F5E9',
                        'color': C['danger'] if acc == 'Yes' else C['success'],
                        'padding': '3px 10px', 'borderRadius': '12px',
                        'fontSize': '12px', 'fontWeight': '700',
                    }),
                    style={'padding': '9px 12px', 'textAlign': 'center'}
                ),
                html.Td(
                    html.Span(r.get('signed_contract', 'No'), style={
                        'background': '#E8F5E9' if r.get('signed_contract') == 'Yes' else '#FFEBEE',
                        'color': C['success'] if r.get('signed_contract') == 'Yes' else C['danger'],
                        'padding': '3px 10px', 'borderRadius': '12px',
                        'fontSize': '12px', 'fontWeight': '700',
                    }),
                    style={'padding': '9px 12px', 'textAlign': 'center'}
                ),
            ], style={'borderBottom': f'1px solid {C["border"]}',
                      'background': '#FFF8E1' if acc == 'Yes' else 'white'}))

        return html.Table([
            html.Thead(html.Tr([
                html.Th(h, style={
                    'padding': '10px 12px', 'fontSize': '11px', 'fontWeight': '700',
                    'textTransform': 'uppercase', 'letterSpacing': '1px', 'color': C['muted'],
                    'background': C['light_bg'], 'borderBottom': f'2px solid {C["border"]}',
                }) for h in ['Name', 'Site', 'Category', 'Role', 'Gender',
                             'Age', 'Had Accident', 'Contract']
            ])),
            html.Tbody(rows),
        ], style={'width': '100%', 'borderCollapse': 'collapse', 'fontSize': '13px'})

    # ── PAYMENT FREQUENCY ─────────────────────────────────────────────────────
    @app.callback(
        Output('w-payment-freq', 'figure'),
        Input('workers-site-filter',   'value'),
        Input('workers-role-filter',   'value'),
        Input('workers-gender-filter', 'value'),
    )
    def payment_freq(site, role, gender):
        df = get_df(site, role, gender)
        if df.empty:
            return go.Figure()
        counts = df['payment_frequency'].value_counts()
        fig = go.Figure(go.Pie(
            labels=counts.index, values=counts.values, hole=0.55,
            marker_colors=PALETTE[:len(counts)],
            textinfo='label+percent',
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

    # ── PAYMENT BY SITE ───────────────────────────────────────────────────────
    @app.callback(
        Output('w-payment-site', 'figure'),
        Input('workers-site-filter',   'value'),
        Input('workers-role-filter',   'value'),
        Input('workers-gender-filter', 'value'),
    )
    def payment_site(site, role, gender):
        df = get_df(site, role, gender)
        if df.empty:
            return go.Figure()

        freq_order = ['Daily', 'Weekly', 'Bi-weekly', 'Monthly']
        sites      = df['site_name'].value_counts().index.tolist()
        freq_colors = {
            'Daily':    C['p4'],
            'Weekly':   C['p3'],
            'Bi-weekly': C['p2'],
            'Monthly':  C['p1'],
        }

        fig = go.Figure()
        for freq in freq_order:
            vals = [df[(df['site_name'] == s) & (df['payment_frequency'] == freq)].shape[0]
                    for s in sites]
            if sum(vals) == 0:
                continue
            fig.add_trace(go.Bar(
                name=freq, x=sites, y=vals,
                marker_color=freq_colors.get(freq, C['muted']),
                marker_line_width=0,
            ))
        fig.update_layout(**BASE_LAYOUT, barmode='stack')
        fig.update_xaxes(tickangle=-30)
        fig.update_yaxes(title='Number of Workers')
        return fig

    # ── GRIEVANCE CHANNEL ─────────────────────────────────────────────────────
    @app.callback(
        Output('w-grievance-channel', 'figure'),
        Input('workers-site-filter',   'value'),
        Input('workers-role-filter',   'value'),
        Input('workers-gender-filter', 'value'),
    )
    def grievance_channel(site, role, gender):
        df = get_df(site, role, gender)
        if df.empty:
            return go.Figure()

        def simplify(ch):
            ch = str(ch)
            if 'Grievance Redress' in ch or 'GRC' in ch:
                return 'Grievance Redress Committee'
            elif 'foreman' in ch.lower():
                return 'Reported to Foreman'
            elif 'company' in ch.lower() or 'administration' in ch.lower():
                return 'Company Administration'
            elif 'District' in ch:
                return 'District Office'
            elif 'Cell' in ch:
                return 'Cell Administration'
            elif 'Sector' in ch:
                return 'Sector Administration'
            return 'Other / None'

        counts = df['grievance_channel'].apply(simplify).value_counts()
        n      = len(df)
        pcts   = counts.values / n * 100

        fig = go.Figure(go.Bar(
            y=counts.index, x=pcts, orientation='h',
            marker_color=PALETTE[:len(counts)], marker_line_width=0,
            text=[f'{p:.0f}% ({v})' for p, v in zip(pcts, counts.values)],
            textposition='outside', textfont=dict(size=12),
        ))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_xaxes(range=[0, 80], ticksuffix='%', title='% of Workers')
        return fig

    # ── GRM vs CONTRACT ───────────────────────────────────────────────────────
    @app.callback(
        Output('w-grm-contract', 'figure'),
        Input('workers-site-filter',   'value'),
        Input('workers-role-filter',   'value'),
        Input('workers-gender-filter', 'value'),
    )
    def grm_contract(site, role, gender):
        df = get_df(site, role, gender)
        if df.empty:
            return go.Figure()

        def knows_grc(ch):
            return 'Grievance Redress' in str(ch) or 'GRC' in str(ch)

        df['knows_grc'] = df['grievance_channel'].apply(knows_grc)
        data = df.groupby('signed_contract').apply(
            lambda x: pd.Series({
                'grc_aware_pct': x['knows_grc'].mean() * 100,
                'count': len(x),
            })
        ).reset_index()

        colors = [C['success'] if r >= 60 else C['danger'] for r in data['grc_aware_pct']]

        fig = go.Figure(go.Bar(
            x=[f'{s} Contract (n={int(c)})' for s, c
               in zip(data['signed_contract'], data['count'])],
            y=data['grc_aware_pct'],
            marker_color=colors, marker_line_width=0,
            text=[f'{r:.0f}%' for r in data['grc_aware_pct']],
            textposition='outside', textfont=dict(size=14),
        ))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_yaxes(title='% Aware of GRC', ticksuffix='%', range=[0, 100])
        return fig

    # ── SITE RISK SCORING TABLE ───────────────────────────────────────────────
    @app.callback(
        Output('w-site-risk', 'children'),
        Input('workers-site-filter',   'value'),
        Input('workers-role-filter',   'value'),
        Input('workers-gender-filter', 'value'),
    )
    def site_risk(site, role, gender):
        df = get_df(site, role, gender)
        if df.empty:
            return html.Div('No data available.', style={'color': C['muted']})

        def score_color(pct):
            if pct >= 75:
                return C['success'], '#E8F5E9'
            elif pct >= 50:
                return C['warning'], '#FFF3E0'
            return C['danger'], '#FFEBEE'

        def bar(pct, color):
            return html.Div([
                html.Div([
                    html.Div(style={
                        'width': f'{min(pct, 100):.0f}%',
                        'height': '6px',
                        'background': color,
                        'borderRadius': '3px',
                    }),
                ], style={
                    'background': C['border'], 'borderRadius': '3px',
                    'overflow': 'hidden', 'width': '80px',
                    'display': 'inline-block', 'verticalAlign': 'middle',
                    'marginRight': '6px',
                }),
                html.Span(f'{pct:.0f}%', style={
                    'fontSize': '12px', 'fontWeight': '700',
                    'color': color, 'verticalAlign': 'middle',
                }),
            ])

        # Compute scores per site
        rows = []
        for s in df.groupby('site_name').size().sort_values(ascending=False).index:
            sub = df[df['site_name'] == s]
            cat = sub['site_category'].iloc[0]
            n   = len(sub)

            contract  = float(sub['signed_contract'].eq('Yes').mean() * 100)
            conduct   = float(sub['code_of_conduct'].eq('Yes').mean() * 100)
            insurance = float(sub['health_insurance'].eq('Yes').mean() * 100)
            training  = float(sub['train_score'].mean() / 5 * 100)
            safety    = float(sub['accident_occurred'].eq('No').mean() * 100)
            ppe       = float(sub['ppe_received'].eq('Yes').mean() * 100)
            global_score = (contract + conduct + insurance + training + safety + ppe) / 6

            gc, gb = score_color(global_score)

            rows.append(html.Tr([
                # Site name + category badge
                html.Td([
                    html.Div(s, style={
                        'fontWeight': '700', 'fontSize': '13px',
                        'color': C['primary'], 'marginBottom': '3px',
                    }),
                    html.Span(cat, style={
                        'background': CAT_COLORS.get(cat, C['muted']) + '22',
                        'color': CAT_COLORS.get(cat, C['muted']),
                        'padding': '1px 8px', 'borderRadius': '10px',
                        'fontSize': '10px', 'fontWeight': '700',
                    }),
                ], style={'padding': '10px 12px'}),
                # n workers
                html.Td(str(n), style={
                    'fontSize': '13px', 'textAlign': 'center',
                    'padding': '10px 8px', 'color': C['muted'],
                }),
                # Individual indicators
                *[html.Td(bar(v, score_color(v)[0]), style={'padding': '10px 8px'})
                  for v in [contract, conduct, insurance, training, safety, ppe]],
                # Global score
                html.Td(
                    html.Span(f'{global_score:.0f}%', style={
                        'background': gb, 'color': gc,
                        'padding': '4px 12px', 'borderRadius': '12px',
                        'fontSize': '13px', 'fontWeight': '900',
                    }),
                    style={'padding': '10px 12px', 'textAlign': 'center'},
                ),
            ], style={
                'borderBottom': f'1px solid {C["border"]}',
                'background': '#FFEBEE' if global_score < 50 else 'white',
            }))

        headers = ['Site', 'n', 'Contract', 'Code of Conduct',
                   'Insurance', 'Training', 'Safety', 'PPE', 'Global Score']

        return html.Table([
            html.Thead(html.Tr([
                html.Th(h, style={
                    'padding': '10px 12px', 'fontSize': '11px', 'fontWeight': '700',
                    'textTransform': 'uppercase', 'letterSpacing': '1px',
                    'color': C['muted'], 'background': C['light_bg'],
                    'borderBottom': f'2px solid {C["border"]}',
                    'textAlign': 'center' if h not in ['Site'] else 'left',
                }) for h in headers
            ])),
            html.Tbody(rows),
        ], style={'width': '100%', 'borderCollapse': 'collapse', 'fontSize': '13px'})

    # ── RISK SUMMARY ──────────────────────────────────────────────────────────
    @app.callback(
        Output('w-risk-summary', 'children'),
        Input('workers-site-filter',   'value'),
        Input('workers-role-filter',   'value'),
        Input('workers-gender-filter', 'value'),
    )
    def risk_summary(site, role, gender):
        df = get_df(site, role, gender)
        if df.empty:
            return html.Div('—')
        n = len(df)
        indicators = [
            ('No Signed Contract',   df['signed_contract'].eq('No').sum()),
            ('No Code of Conduct',   df['code_of_conduct'].eq('No').sum()),
            ('No Health Insurance',  df['health_insurance'].eq('No').sum()),
            ('No PPE Provided',      df['ppe_received'].eq('No').sum()),
            ('Zero Training',        df['training_count'].eq(0).sum()),
            ('Experienced Accident', df['accident_occurred'].eq('Yes').sum()),
            ('3+ Rights Deficits',   df['vuln_score'].ge(3).sum()),
        ]
        items = []
        for label, count in indicators:
            pct   = count / n * 100
            color = C['success'] if count == 0 else (C['warning'] if pct < 25 else C['danger'])
            items.append(html.Div([
                html.Div([
                    html.Span(label, style={
                        'fontSize': '13px', 'fontWeight': '600', 'color': C['primary'],
                    }),
                    html.Span(f'{count} workers', style={
                        'fontSize': '13px', 'fontWeight': '800', 'color': color,
                    }),
                ], style={'display': 'flex', 'justifyContent': 'space-between',
                          'marginBottom': '4px'}),
                html.Div([
                    html.Div(style={
                        'width': f'{min(pct, 100):.1f}%', 'height': '5px',
                        'background': color, 'borderRadius': '3px',
                    }),
                ], style={'background': C['border'], 'borderRadius': '3px',
                          'overflow': 'hidden'}),
            ], style={'marginBottom': '13px'}))
        return html.Div(items)