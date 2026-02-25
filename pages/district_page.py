"""
IMCE Dashboard — District Page
Filters: District → Site
Sections: KPIs, Impacts, Compensation, Instruments & Staff,
          GRM Analysis, Pending Blockers, Scoring Table
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

INST_COLS = [
    'inst_esmf_rpf', 'inst_lmp', 'inst_sep',
    'inst_esia', 'inst_esmf', 'inst_gbv_sea_plan',
    'permit_eia_cert', 'permit_eia_conditions', 'permit_borrow_pit',
]
INST_LABELS = [
    'ESMF/RPF', 'LMP', 'SEP',
    'ESIA', 'ESMF', 'GBV/SEA Plan',
    'EIA Certificate', 'EIA Conditions', 'Borrow Pit Permit',
]

IMPACT_COLS = [
    'impact_physical_displacement', 'impact_loss_structures',
    'impact_loss_land', 'impact_loss_crops_trees',
    'impact_loss_business', 'impact_other',
]
IMPACT_LABELS = [
    'Physical Displacement', 'Loss of Structures',
    'Loss of Land', 'Loss of Crops/Trees',
    'Loss of Business', 'Other',
]

GRM_FACIL_COLS   = ['grm_facil_materials', 'grm_facil_transport',
                    'grm_facil_communication', 'grm_facil_per_diem']
GRM_FACIL_LABELS = ['Materials', 'Transport', 'Communication', 'Per Diem']

GRM_MEMBER_COLS   = ['grm_member_paps_rep', 'grm_member_local_admin',
                     'grm_member_project_staff', 'grm_member_contractors',
                     'grm_member_other']
GRM_MEMBER_LABELS = ['PAPs Representative', 'Local Admin',
                     'Project Staff', 'Contractors', 'Other']

# ─────────────────────────────────────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────────────────────────────────────

def load_district():
    import os
    paths = [
        'district_clean.csv',
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'district_clean.csv'),
    ]
    df = pd.DataFrame()
    for p in paths:
        if os.path.exists(p):
            df = pd.read_csv(p)
            break
    if df.empty:
        return df

    df['district_name'] = df['district_name'].str.strip()
    df['site_name']     = df['site_name'].str.strip()

    # Compensation rate capped at 100
    df['compensation_rate'] = pd.to_numeric(
        df['compensation_progress'], errors='coerce').clip(upper=100).fillna(0)

    # Instrument score
    df['inst_score'] = df[INST_COLS].sum(axis=1) / len(INST_COLS) * 100

    # Staff score (env + social dedicated specialists)
    df['staff_score'] = (
        (df['staff_env_specialist'] + df['staff_social_specialist']) / 2 * 100
    )

    # GRM facilitation score
    df['grm_facil_score'] = df[GRM_FACIL_COLS].sum(axis=1) / len(GRM_FACIL_COLS) * 100

    # Global composite score
    df['global_score'] = (
        df['compensation_rate'] * 0.35 +
        df['inst_score']        * 0.25 +
        df['staff_score']       * 0.20 +
        df['grm_facil_score']   * 0.20
    )

    # Compensation anomaly flag: non compensated > households affected
    df['comp_anomaly'] = (
        df['not_yet_compensated_count'] > df['households_affected']
    )

    return df


DIST = load_district()


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


def get_df(district, site):
    df = DIST.copy()
    if df.empty:
        return df
    if district and district != 'ALL':
        df = df[df['district_name'] == district]
    if site and site != 'ALL':
        df = df[df['site_name'] == site]
    return df


def alert_banner(text, color=C['danger'], bg='#FFEBEE'):
    return html.Div([
        html.Span('⚠️  ', style={'fontSize': '15px'}),
        html.Span(text, style={
            'fontSize': '13px', 'fontWeight': '700', 'color': color,
        }),
    ], style={
        'background': bg, 'border': f'1px solid {color}',
        'borderRadius': '8px', 'padding': '10px 16px',
        'marginBottom': '16px',
    })


# ─────────────────────────────────────────────────────────────────────────────
# FILTER BAR
# ─────────────────────────────────────────────────────────────────────────────

def filter_bar():
    districts = sorted(DIST['district_name'].unique().tolist()) if not DIST.empty else []
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
                id='dist-district-filter',
                options=[{'label': 'All Districts', 'value': 'ALL'}] +
                        [{'label': d, 'value': d} for d in districts],
                value='ALL', clearable=False, style=dd,
            ),
        ]),
        html.Div([
            html.Label('Site', style=lbl),
            dcc.Dropdown(
                id='dist-site-filter',
                options=[{'label': 'All Sites', 'value': 'ALL'}],
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
    if DIST.empty:
        return html.Div('district_clean.csv not found.',
                        style={'padding': '40px 40px 40px 260px'})

    # Overall status badge
    avg_score = float(DIST['global_score'].mean())
    critical  = int((DIST['compensation_rate'] < 30).sum())

    if critical > 0:
        sc, st, sb = C['danger'], f'⚠ {critical} CRITICAL DISTRICT(S)', '#FFEBEE'
    elif avg_score >= 70:
        sc, st, sb = C['success'], '● ON TRACK', '#E8F5E9'
    else:
        sc, st, sb = C['warning'], '● ATTENTION REQUIRED', '#FFF3E0'

    return html.Div([

        # PAGE HEADER
        html.Div([
            html.Div([
                html.H2('District Monitoring', style={
                    'margin': '0 0 4px 0', 'fontWeight': '900',
                    'fontSize': '26px', 'color': C['primary'],
                }),
                html.P(
                    f'{len(DIST)} districts monitored — '
                    f'{int(DIST["households_affected"].sum())} total households affected — IMCE Project Rwanda',
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

        # CRITICAL ALERTS (static, always visible)
        html.Div(id='dist-alerts'),

        # SECTION 1 — KPIs
        dbc.Row([
            dbc.Col(html.Div(id='d-kpi-districts'),   md=2),
            dbc.Col(html.Div(id='d-kpi-households'),  md=2),
            dbc.Col(html.Div(id='d-kpi-comp-rate'),   md=2),
            dbc.Col(html.Div(id='d-kpi-pending'),     md=2),
            dbc.Col(html.Div(id='d-kpi-displaced'),   md=2),
            dbc.Col(html.Div(id='d-kpi-grm-total'),   md=2),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 2 — Compensation (CORE)
        dbc.Row([
            dbc.Col([card([
                section_title('Compensation Rate by District',
                              'Critical World Bank indicator — % of eligible PAPs compensated'),
                dcc.Graph(id='d-comp-rate',
                          config={'displayModeBar': False}, style={'height': '280px'}),
            ])], md=7),
            dbc.Col([card([
                section_title('Compensation Timing',
                              'When was compensation disbursed relative to construction?'),
                dcc.Graph(id='d-comp-timing',
                          config={'displayModeBar': False}, style={'height': '280px'}),
            ])], md=5),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 3 — Pending Blockers
        dbc.Row([
            dbc.Col([card([
                section_title('Pending Households by District',
                              'Number of households awaiting compensation — with root cause'),
                dcc.Graph(id='d-pending-bar',
                          config={'displayModeBar': False}, style={'height': '260px'}),
            ])], md=6),
            dbc.Col([card([
                section_title('Why Are PAPs Still Uncompensated?',
                              'Root causes blocking compensation per district'),
                html.Div(id='d-pending-reasons'),
            ])], md=6),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 4 — Impacts
        dbc.Row([
            dbc.Col([card([
                section_title('Impact Profile by District',
                              'Types and magnitude of impacts per project site'),
                dcc.Graph(id='d-impact-stacked',
                          config={'displayModeBar': False}, style={'height': '300px'}),
            ])], md=8),
            dbc.Col([card([
                section_title('Displacement Overview',
                              'Physical displacement vs total households affected'),
                dcc.Graph(id='d-displacement',
                          config={'displayModeBar': False}, style={'height': '300px'}),
            ])], md=4),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 5 — Instruments & Staff
        dbc.Row([
            dbc.Col([card([
                section_title('E&S Instruments Heatmap',
                              'Which district has which instrument in place? Red = missing, critical gap'),
                html.Div(id='d-instruments-heatmap'),
            ])], md=8),
            dbc.Col([card([
                section_title('Dedicated E&S Staff',
                              'Environmental & Social Specialist presence by district'),
                dcc.Graph(id='d-staff-chart',
                          config={'displayModeBar': False}, style={'height': '280px'}),
            ])], md=4),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 6 — GRM
        dbc.Row([
            dbc.Col([card([
                section_title('GRM Count & Coverage Level',
                              'Number of GRMs and whether cell and sector levels are covered'),
                dcc.Graph(id='d-grm-count',
                          config={'displayModeBar': False}, style={'height': '260px'}),
            ])], md=4),
            dbc.Col([card([
                section_title('GRM Facilitation Resources',
                              'Which districts provide materials, transport, communication, per diem to GRC members'),
                dcc.Graph(id='d-grm-facil',
                          config={'displayModeBar': False}, style={'height': '260px'}),
            ])], md=4),
            dbc.Col([card([
                section_title('GRM Composition',
                              'Who sits on the GRM? PAPs rep, admin, project staff, contractors'),
                dcc.Graph(id='d-grm-composition',
                          config={'displayModeBar': False}, style={'height': '260px'}),
            ])], md=4),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 7 — Scoring Table
        dbc.Row([
            dbc.Col([card([
                section_title('District Performance Scoring',
                              'Composite: Compensation (35%) + Instruments (25%) + Staff (20%) + GRM Facilitation (20%)'),
                html.Div(id='d-scoring-table'),
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

    # ── CASCADE: site options ─────────────────────────────────────────────────
    @app.callback(
        Output('dist-site-filter', 'options'),
        Output('dist-site-filter', 'value'),
        Input('dist-district-filter', 'value'),
    )
    def update_site_options(district):
        df = DIST.copy()
        if district and district != 'ALL':
            df = df[df['district_name'] == district]
        sites = sorted(df['site_name'].dropna().unique().tolist())
        options = [{'label': 'All Sites', 'value': 'ALL'}] + \
                  [{'label': s, 'value': s} for s in sites]
        return options, 'ALL'

    # ── CRITICAL ALERTS ───────────────────────────────────────────────────────
    @app.callback(
        Output('dist-alerts', 'children'),
        Input('dist-district-filter', 'value'),
        Input('dist-site-filter',     'value'),
    )
    def update_alerts(district, site):
        df = get_df(district, site)
        alerts = []

        # Anomaly: non compensated > households affected
        anomaly = df[df['comp_anomaly'] == True]
        for _, r in anomaly.iterrows():
            alerts.append(alert_banner(
                f"{r['district_name']} — {int(r['not_yet_compensated_count'])} households pending "
                f"vs only {int(r['households_affected'])} registered: likely a cross-phase backlog. "
                f"Immediate World Bank escalation required.",
                C['danger'], '#FFEBEE'
            ))

        # Critical compensation < 30%
        critical = df[(df['compensation_rate'] < 30) & (~df['comp_anomaly'])]
        for _, r in critical.iterrows():
            alerts.append(alert_banner(
                f"{r['district_name']} ({r['site_name']}) — Compensation rate at "
                f"{r['compensation_rate']:.0f}% — {int(r['not_yet_compensated_count'])} "
                f"households still pending. Action required.",
                C['danger'], '#FFEBEE'
            ))

        # Missing critical instruments
        for _, r in df.iterrows():
            missing = [INST_LABELS[i] for i, c in enumerate(INST_COLS) if r[c] == 0]
            if len(missing) >= 3:
                alerts.append(alert_banner(
                    f"{r['district_name']} — {len(missing)} E&S instruments missing: "
                    f"{', '.join(missing[:4])}{'...' if len(missing) > 4 else ''}. "
                    f"Compliance gap — corrective action needed.",
                    C['warning'], '#FFF3E0'
                ))

        # No dedicated E&S staff
        no_staff = df[(df['staff_env_specialist'] == 0) & (df['staff_social_specialist'] == 0)]
        for _, r in no_staff.iterrows():
            alerts.append(alert_banner(
                f"{r['district_name']} — No dedicated Environmental or Social Specialist. "
                f"Role covered by general staff. Structural fragility.",
                C['warning'], '#FFF8E1'
            ))

        return alerts if alerts else html.Span()

    # ── KPIs ─────────────────────────────────────────────────────────────────
    @app.callback(
        Output('d-kpi-districts',  'children'),
        Output('d-kpi-households', 'children'),
        Output('d-kpi-comp-rate',  'children'),
        Output('d-kpi-pending',    'children'),
        Output('d-kpi-displaced',  'children'),
        Output('d-kpi-grm-total',  'children'),
        Input('dist-district-filter', 'value'),
        Input('dist-site-filter',     'value'),
    )
    def update_kpis(district, site):
        df = get_df(district, site)
        if df.empty:
            return [html.Div('—')] * 6

        n             = len(df)
        households    = int(df['households_affected'].sum())
        pending       = int(df['not_yet_compensated_count'].sum())
        displaced     = int(df['impact_physical_displacement'].sum())
        grm_total     = int(df['grm_count'].sum())

        # Weighted avg compensation rate by households
        if households > 0:
            weighted_comp = sum(
                r['compensation_rate'] * r['households_affected']
                for _, r in df.iterrows()
            ) / households
        else:
            weighted_comp = 0

        cc = C['success'] if weighted_comp >= 80 else (
             C['warning'] if weighted_comp >= 60 else C['danger'])
        pc = C['danger']  if pending > 50 else (C['warning'] if pending > 10 else C['success'])
        dc = C['danger']  if displaced > 20 else (C['warning'] if displaced > 0 else C['success'])

        return (
            kpi('Districts', str(n), 'Project sites monitored', C['accent']),
            kpi('Households Affected', str(households), 'Total across all sites', C['p3']),
            kpi('Compensation Rate', f'{weighted_comp:.0f}%',
                'Weighted by households', cc),
            kpi('Pending Households', str(pending),
                'Awaiting compensation', pc),
            kpi('Physically Displaced', str(displaced),
                'Households displaced from homes', dc),
            kpi('GRM Committees', str(grm_total),
                'Total GRMs across districts', C['secondary']),
        )

    # ── COMPENSATION RATE ─────────────────────────────────────────────────────
    @app.callback(
        Output('d-comp-rate', 'figure'),
        Input('dist-district-filter', 'value'),
        Input('dist-site-filter',     'value'),
    )
    def comp_rate(district, site):
        df = get_df(district, site)
        if df.empty:
            return go.Figure()

        data = df.sort_values('compensation_rate', ascending=True)
        colors = [C['danger'] if v < 30 else (C['warning'] if v < 75 else C['success'])
                  for v in data['compensation_rate']]

        fig = go.Figure(go.Bar(
            y=data['district_name'],
            x=data['compensation_rate'],
            orientation='h',
            marker_color=colors, marker_line_width=0,
            text=[f"{v:.0f}%  ({int(p)} pending)"
                  for v, p in zip(data['compensation_rate'],
                                  data['not_yet_compensated_count'])],
            textposition='outside', textfont=dict(size=11),
            customdata=data[['site_name', 'not_yet_compensated_count',
                              'households_affected']].values,
            hovertemplate=(
                '<b>%{y}</b><br>'
                'Site: %{customdata[0]}<br>'
                'Rate: %{x:.0f}%<br>'
                'Pending: %{customdata[1]}<br>'
                'Total HH: %{customdata[2]}<extra></extra>'
            ),
        ))
        fig.add_vline(x=80, line_dash='dot', line_color=C['muted'],
                      annotation_text='80% target',
                      annotation_font=dict(size=11, color=C['muted']))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_xaxes(range=[0, 125], ticksuffix='%', title='Compensation Rate')
        return fig

    # ── COMPENSATION TIMING ───────────────────────────────────────────────────
    @app.callback(
        Output('d-comp-timing', 'figure'),
        Input('dist-district-filter', 'value'),
        Input('dist-site-filter',     'value'),
    )
    def comp_timing(district, site):
        df = get_df(district, site)
        if df.empty:
            return go.Figure()

        def simplify(t):
            t = str(t).lower()
            if 'before' in t and 'during' not in t and 'after' not in t:
                return 'Before construction'
            elif 'before' in t and ('during' in t or 'after' in t):
                return 'Before & during/after'
            elif 'during' in t and 'before' not in t:
                return 'During construction'
            elif 'after' in t:
                return 'After construction'
            return 'Not specified'

        timing = df['compensation_timing'].apply(simplify).value_counts()

        color_map = {
            'Before construction':      C['success'],
            'Before & during/after':    C['p2'],
            'During construction':      C['warning'],
            'After construction':       C['danger'],
            'Not specified':            C['muted'],
        }
        colors = [color_map.get(l, C['muted']) for l in timing.index]

        fig = go.Figure(go.Pie(
            labels=timing.index, values=timing.values,
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
                            font=dict(family='Nunito, sans-serif', size=13)),
        )
        return fig

    # ── PENDING BAR ───────────────────────────────────────────────────────────
    @app.callback(
        Output('d-pending-bar', 'figure'),
        Input('dist-district-filter', 'value'),
        Input('dist-site-filter',     'value'),
    )
    def pending_bar(district, site):
        df = get_df(district, site)
        if df.empty:
            return go.Figure()

        data = df.sort_values('not_yet_compensated_count', ascending=False)
        colors = [C['danger'] if v > 50 else (C['warning'] if v > 10 else C['p2'])
                  for v in data['not_yet_compensated_count']]

        fig = go.Figure(go.Bar(
            x=data['district_name'],
            y=data['not_yet_compensated_count'],
            marker_color=colors, marker_line_width=0,
            text=data['not_yet_compensated_count'].astype(int),
            textposition='outside', textfont=dict(size=12),
            customdata=data[['comp_anomaly', 'households_affected']].values,
            hovertemplate=(
                '<b>%{x}</b><br>'
                'Pending: %{y}<br>'
                'Total HH affected: %{customdata[1]}<br>'
                'Cross-phase anomaly: %{customdata[0]}<extra></extra>'
            ),
        ))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_yaxes(title='Households Pending Compensation')
        return fig

    # ── PENDING REASONS ───────────────────────────────────────────────────────
    @app.callback(
        Output('d-pending-reasons', 'children'),
        Input('dist-district-filter', 'value'),
        Input('dist-site-filter',     'value'),
    )
    def pending_reasons(district, site):
        df = get_df(district, site)
        df = df[df['not_compensated_reason'].notna() &
                (df['not_compensated_reason'].astype(str) != 'nan')]

        if df.empty:
            return html.Div([
                html.Span('✓', style={'fontSize': '24px', 'color': C['success']}),
                html.P('No pending households.',
                       style={'color': C['success'], 'fontWeight': '700',
                              'fontSize': '13px', 'margin': '6px 0 0 0'}),
            ], style={'textAlign': 'center', 'padding': '24px'})

        def categorize(text, pending):
            t = str(text).lower()
            if 'abroad' in t or 'outside' in t or 'soldier' in t or 'foreign' in t:
                cat = '🌍 Beneficiary abroad / unreachable'
                c = C['warning']
            elif 'court' in t or 'succession' in t or 'legal' in t or 'title' in t or 'bank' in t:
                cat = '⚖️ Legal dispute / succession / court'
                c = C['danger']
            elif 'document' in t or 'require' in t or 'fulfill' in t or 'complet' in t:
                cat = '📄 Documentation incomplete'
                c = C['warning']
            elif 'district' in t or 'confirm' in t or 'process' in t or 'month' in t:
                cat = '🏛️ Awaiting district confirmation'
                c = C['p3']
            else:
                cat = '❓ Other administrative reason'
                c = C['muted']
            return cat, c

        items = []
        for _, r in df.sort_values('not_yet_compensated_count', ascending=False).iterrows():
            cat, col = categorize(r['not_compensated_reason'],
                                  r['not_yet_compensated_count'])
            items.append(html.Div([
                html.Div([
                    html.Div(r['district_name'], style={
                        'fontWeight': '800', 'fontSize': '13px', 'color': C['primary'],
                    }),
                    html.Span(
                        f"{int(r['not_yet_compensated_count'])} HH",
                        style={
                            'background': '#FFEBEE', 'color': C['danger'],
                            'padding': '2px 8px', 'borderRadius': '10px',
                            'fontSize': '11px', 'fontWeight': '800',
                        }
                    ),
                ], style={'display': 'flex', 'justifyContent': 'space-between',
                          'alignItems': 'center', 'marginBottom': '4px'}),
                html.Div(cat, style={
                    'fontSize': '12px', 'fontWeight': '700', 'color': col,
                    'marginBottom': '4px',
                }),
                html.P(str(r['not_compensated_reason'])[:180] + ('...' if len(str(r['not_compensated_reason'])) > 180 else ''),
                       style={
                           'fontSize': '11px', 'color': C['muted'],
                           'margin': '0 0 4px 0', 'fontStyle': 'italic',
                           'lineHeight': '1.5',
                       }),
                html.Div(style={'height': '1px', 'background': C['border'],
                                'margin': '8px 0'}),
            ]))

        return html.Div(items, style={'maxHeight': '280px', 'overflowY': 'auto'})

    # ── IMPACT STACKED ────────────────────────────────────────────────────────
    @app.callback(
        Output('d-impact-stacked', 'figure'),
        Input('dist-district-filter', 'value'),
        Input('dist-site-filter',     'value'),
    )
    def impact_stacked(district, site):
        df = get_df(district, site)
        if df.empty:
            return go.Figure()

        fig = go.Figure()
        for col, label, color in zip(IMPACT_COLS, IMPACT_LABELS, PALETTE):
            vals = pd.to_numeric(df[col], errors='coerce').fillna(0)
            fig.add_trace(go.Bar(
                name=label,
                x=df['district_name'],
                y=vals,
                marker_color=color, marker_line_width=0,
                text=vals.astype(int).where(vals > 0, ''),
                textposition='inside',
                textfont=dict(color='white', size=10),
            ))

        fig.update_layout(**BASE_LAYOUT, barmode='stack')
        fig.update_xaxes(tickangle=-15)
        fig.update_yaxes(title='Number of Units Affected')
        return fig

    # ── DISPLACEMENT ─────────────────────────────────────────────────────────
    @app.callback(
        Output('d-displacement', 'figure'),
        Input('dist-district-filter', 'value'),
        Input('dist-site-filter',     'value'),
    )
    def displacement(district, site):
        df = get_df(district, site)
        if df.empty:
            return go.Figure()

        data = df[['district_name', 'households_affected',
                   'impact_physical_displacement']].copy()
        data['not_displaced'] = data['households_affected'] - \
                                pd.to_numeric(data['impact_physical_displacement'],
                                              errors='coerce').fillna(0)
        data = data.sort_values('households_affected', ascending=False)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Physically Displaced',
            x=data['district_name'],
            y=pd.to_numeric(data['impact_physical_displacement'], errors='coerce').fillna(0),
            marker_color=C['danger'], marker_line_width=0,
            text=pd.to_numeric(data['impact_physical_displacement'],
                                errors='coerce').fillna(0).astype(int),
            textposition='inside', textfont=dict(color='white', size=11),
        ))
        fig.add_trace(go.Bar(
            name='Other Impact',
            x=data['district_name'],
            y=data['not_displaced'].clip(lower=0),
            marker_color=C['p3'], marker_line_width=0,
        ))
        fig.update_layout(**BASE_LAYOUT, barmode='stack')
        fig.update_xaxes(tickangle=-15)
        fig.update_yaxes(title='Households')
        return fig

    # ── INSTRUMENTS HEATMAP ───────────────────────────────────────────────────
    @app.callback(
        Output('d-instruments-heatmap', 'children'),
        Input('dist-district-filter', 'value'),
        Input('dist-site-filter',     'value'),
    )
    def instruments_heatmap(district, site):
        df = get_df(district, site)
        if df.empty:
            return html.Div('No data.')

        header_cells = [
            html.Th('District', style={
                'padding': '8px 12px', 'fontSize': '11px', 'fontWeight': '700',
                'textTransform': 'uppercase', 'letterSpacing': '1px',
                'color': C['muted'], 'background': C['light_bg'],
                'borderBottom': f'2px solid {C["border"]}',
                'textAlign': 'left', 'minWidth': '130px',
            })
        ] + [
            html.Th(lbl, style={
                'padding': '8px 10px', 'fontSize': '10px', 'fontWeight': '700',
                'textTransform': 'uppercase', 'letterSpacing': '0.5px',
                'color': C['muted'], 'background': C['light_bg'],
                'borderBottom': f'2px solid {C["border"]}',
                'textAlign': 'center', 'minWidth': '75px',
                'borderLeft': f'1px solid {C["border"]}',
            }) for lbl in INST_LABELS
        ] + [
            html.Th('Score', style={
                'padding': '8px 10px', 'fontSize': '11px', 'fontWeight': '700',
                'textTransform': 'uppercase',
                'color': C['muted'], 'background': C['light_bg'],
                'borderBottom': f'2px solid {C["border"]}',
                'textAlign': 'center', 'minWidth': '65px',
                'borderLeft': f'2px solid {C["border"]}',
            })
        ]

        rows = []
        for _, r in df.iterrows():
            score = float(r['inst_score'])
            sc, sb = score_color(score)
            cells = [
                html.Td([
                    html.Div(r['district_name'], style={
                        'fontWeight': '700', 'fontSize': '12px', 'color': C['primary'],
                    }),
                    html.Div(r['site_name'], style={
                        'fontSize': '10px', 'color': C['muted'], 'fontStyle': 'italic',
                    }),
                ], style={'padding': '10px 12px'}),
            ]
            for col in INST_COLS:
                val = int(r[col]) if pd.notna(r[col]) else 0
                cells.append(html.Td(
                    html.Span(
                        '✓' if val else '✗',
                        style={
                            'fontSize': '16px', 'fontWeight': '900',
                            'color': C['success'] if val else C['danger'],
                        }
                    ),
                    style={
                        'textAlign': 'center', 'padding': '10px 8px',
                        'background': '#E8F5E9' if val else '#FFEBEE',
                        'borderLeft': f'1px solid {C["border"]}',
                    }
                ))
            cells.append(html.Td(
                html.Span(f'{score:.0f}%', style={
                    'background': sb, 'color': sc,
                    'padding': '3px 10px', 'borderRadius': '10px',
                    'fontSize': '12px', 'fontWeight': '800',
                }),
                style={'textAlign': 'center', 'padding': '10px 8px',
                       'borderLeft': f'2px solid {C["border"]}'}
            ))
            rows.append(html.Tr(cells, style={
                'borderBottom': f'1px solid {C["border"]}',
            }))

        return html.Table(
            [html.Thead(html.Tr(header_cells)), html.Tbody(rows)],
            style={'width': '100%', 'borderCollapse': 'collapse',
                   'fontSize': '13px', 'overflowX': 'auto'}
        )

    # ── STAFF CHART ───────────────────────────────────────────────────────────
    @app.callback(
        Output('d-staff-chart', 'figure'),
        Input('dist-district-filter', 'value'),
        Input('dist-site-filter',     'value'),
    )
    def staff_chart(district, site):
        df = get_df(district, site)
        if df.empty:
            return go.Figure()

        fig = go.Figure()
        for col, label, color in [
            ('staff_env_specialist',    'Env. Specialist',    C['accent']),
            ('staff_social_specialist', 'Social Specialist',  C['secondary']),
            ('staff_other',             'Other E&S Staff',    C['p3']),
        ]:
            fig.add_trace(go.Bar(
                name=label,
                x=df['district_name'],
                y=df[col].fillna(0),
                marker_color=color, marker_line_width=0,
            ))
        fig.update_layout(**BASE_LAYOUT, barmode='group')
        fig.update_xaxes(tickangle=-15)
        fig.update_yaxes(title='Staff Count (0=None, 1=Present)')
        return fig

    # ── GRM COUNT ─────────────────────────────────────────────────────────────
    @app.callback(
        Output('d-grm-count', 'figure'),
        Input('dist-district-filter', 'value'),
        Input('dist-site-filter',     'value'),
    )
    def grm_count(district, site):
        df = get_df(district, site)
        if df.empty:
            return go.Figure()

        data = df.sort_values('grm_count', ascending=False)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='GRM Count',
            x=data['district_name'],
            y=data['grm_count'],
            marker_color=C['accent'], marker_line_width=0,
            text=data['grm_count'], textposition='outside',
            textfont=dict(size=12),
        ))
        # Overlay sector-level coverage as scatter
        sector_y = [1.5 if v else 0 for v in data['grm_level_sector']]
        fig.add_trace(go.Scatter(
            name='Sector Level ✓',
            x=data['district_name'], y=data['grm_count'],
            mode='markers',
            marker=dict(
                symbol=['star' if v else 'circle-open' for v in data['grm_level_sector']],
                color=[C['secondary'] if v else C['muted'] for v in data['grm_level_sector']],
                size=14, line=dict(width=2, color='white'),
            ),
        ))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_xaxes(tickangle=-15)
        fig.update_yaxes(title='Number of GRMs')
        return fig

    # ── GRM FACILITATION ──────────────────────────────────────────────────────
    @app.callback(
        Output('d-grm-facil', 'figure'),
        Input('dist-district-filter', 'value'),
        Input('dist-site-filter',     'value'),
    )
    def grm_facil(district, site):
        df = get_df(district, site)
        if df.empty:
            return go.Figure()

        n = len(df)
        vals = [int(df[col].sum()) for col in GRM_FACIL_COLS]
        pcts = [v / n * 100 for v in vals]
        colors = [C['success'] if p >= 60 else (C['warning'] if p >= 40 else C['danger'])
                  for p in pcts]

        fig = go.Figure(go.Bar(
            y=GRM_FACIL_LABELS, x=pcts,
            orientation='h',
            marker_color=colors, marker_line_width=0,
            text=[f'{v}/{n} ({p:.0f}%)' for v, p in zip(vals, pcts)],
            textposition='outside', textfont=dict(size=11),
        ))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_xaxes(range=[0, 115], ticksuffix='%',
                         title='% of Districts Providing')
        return fig

    # ── GRM COMPOSITION ───────────────────────────────────────────────────────
    @app.callback(
        Output('d-grm-composition', 'figure'),
        Input('dist-district-filter', 'value'),
        Input('dist-site-filter',     'value'),
    )
    def grm_composition(district, site):
        df = get_df(district, site)
        if df.empty:
            return go.Figure()

        fig = go.Figure()
        for i, (dist_row) in enumerate(df.iterrows()):
            _, r = dist_row
            vals = [int(r[col]) for col in GRM_MEMBER_COLS]
            fig.add_trace(go.Bar(
                name=r['district_name'],
                x=GRM_MEMBER_LABELS,
                y=vals,
                marker_color=PALETTE[i % len(PALETTE)], marker_line_width=0,
            ))

        fig.update_layout(**BASE_LAYOUT, barmode='group')
        fig.update_xaxes(tickangle=-20)
        fig.update_yaxes(title='Present (1) / Absent (0)', range=[0, 1.5])
        return fig

    # ── SCORING TABLE ─────────────────────────────────────────────────────────
    @app.callback(
        Output('d-scoring-table', 'children'),
        Input('dist-district-filter', 'value'),
        Input('dist-site-filter',     'value'),
    )
    def scoring_table(district, site):
        df = get_df(district, site)
        if df.empty:
            return html.Div('No data.')

        data = df.sort_values('global_score', ascending=False)

        def check(val):
            return html.Span('✓' if val else '✗', style={
                'fontSize': '14px', 'fontWeight': '900',
                'color': C['success'] if val else C['danger'],
            })

        rows = []
        for _, r in data.iterrows():
            gc, gb = score_color(float(r['global_score']))
            anomaly_flag = '⚠️' if r['comp_anomaly'] else ''

            rows.append(html.Tr([
                # District
                html.Td([
                    html.Div(f"{r['district_name']} {anomaly_flag}", style={
                        'fontWeight': '700', 'fontSize': '12px', 'color': C['primary'],
                    }),
                    html.Div(r['site_name'], style={
                        'fontSize': '10px', 'color': C['muted'], 'fontStyle': 'italic',
                    }),
                ], style={'padding': '10px 12px', 'minWidth': '160px'}),
                # HH affected
                html.Td(
                    html.Span(str(int(r['households_affected'])),
                              style={'fontWeight': '700', 'fontSize': '13px'}),
                    style={'padding': '10px 8px', 'textAlign': 'center'},
                ),
                # Compensation
                html.Td(prog_bar(r['compensation_rate'],
                                 C['danger'] if r['compensation_rate'] < 30
                                 else (C['warning'] if r['compensation_rate'] < 75
                                       else C['success'])),
                        style={'padding': '10px 8px'}),
                # Pending
                html.Td(
                    html.Span(
                        str(int(r['not_yet_compensated_count'])),
                        style={
                            'fontWeight': '800', 'fontSize': '13px',
                            'color': C['danger'] if r['not_yet_compensated_count'] > 30
                                     else (C['warning'] if r['not_yet_compensated_count'] > 5
                                           else C['success']),
                        }
                    ),
                    style={'padding': '10px 8px', 'textAlign': 'center'},
                ),
                # Instruments
                html.Td(prog_bar(r['inst_score'],
                                 score_color(float(r['inst_score']))[0]),
                        style={'padding': '10px 8px'}),
                # Staff env
                html.Td(check(r['staff_env_specialist']),
                        style={'padding': '10px 8px', 'textAlign': 'center'}),
                # Staff social
                html.Td(check(r['staff_social_specialist']),
                        style={'padding': '10px 8px', 'textAlign': 'center'}),
                # GRM count
                html.Td(
                    html.Span(str(int(r['grm_count'])),
                              style={'fontWeight': '700', 'fontSize': '13px',
                                     'color': C['accent']}),
                    style={'padding': '10px 8px', 'textAlign': 'center'},
                ),
                # GRM facilitation
                html.Td(prog_bar(r['grm_facil_score'],
                                 score_color(float(r['grm_facil_score']))[0]),
                        style={'padding': '10px 8px'}),
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
                'background': '#FFEBEE' if float(r['global_score']) < 50 or r['comp_anomaly']
                              else 'white',
            }))

        headers = [
            'District / Site', 'HH Affected', 'Compensation (35%)',
            'Pending HH', 'Instruments (25%)', 'Env. Staff', 'Social Staff',
            'GRM Count', 'GRM Facilitation (20%)', 'Global Score',
        ]

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