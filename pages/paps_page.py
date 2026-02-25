"""
IMCE Dashboard — PAPs Page (Full Deep Analysis)
Fixes: xaxis conflict in impact_multiplicity
New:   3 cascaded filters (district → sector → site_name), larger fonts
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

def load_paps():
    import os
    paths = [
        'PAPs_clean.csv',
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'PAPs_clean.csv'),
    ]
    df = pd.DataFrame()
    for p in paths:
        if os.path.exists(p):
            df = pd.read_csv(p)
            break
    if df.empty:
        return df

    district_map = {
        'MUSANZE': 'Musanze', 'KICUKIRO': 'Kicukiro',
        'Gasbo': 'Gasabo', 'Gasabo-': 'Gasabo',
        'Nyarungege': 'Nyarugenge', 'Nyarugenge ': 'Nyarugenge',
    }
    df['district'] = df['district'].str.strip().replace(district_map)
    df['site_name'] = df['site_name'].str.strip().replace({'Gasabo- Wetland': 'Gasabo-Wetland'})
    df['sector']    = df['sector'].str.strip()

    impact_cols = ['impact_loss_land', 'impact_loss_house',
                   'impact_loss_structure', 'impact_trees_crops', 'impact_other']
    df['impact_count'] = df[impact_cols].sum(axis=1)
    df['risk_flag'] = (
        (df['compensation_received'] == 'No') |
        (df['compensation_satisfied'] == 'No') |
        (df['grm_aware'] == 'No')
    )
    return df


PAPS = load_paps()


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
        'background': C['card'], 'borderRadius': '12px',
        'padding': '18px 20px',
        'boxShadow': '0 2px 8px rgba(13,33,55,0.07)',
        'borderTop': f'4px solid {color}', 'height': '100%',
    })


def get_df(district, sector, site):
    df = PAPS.copy()
    if df.empty:
        return df
    if district and district != 'ALL':
        df = df[df['district'] == district]
    if sector and sector != 'ALL':
        df = df[df['sector'] == sector]
    if site and site != 'ALL':
        df = df[df['site_name'] == site]
    return df


# ─────────────────────────────────────────────────────────────────────────────
# FILTER BAR
# ─────────────────────────────────────────────────────────────────────────────

def filter_bar():
    districts = sorted(PAPS['district'].unique().tolist()) if not PAPS.empty else []
    dd_style  = {'width': '200px', 'fontFamily': 'Nunito, sans-serif', 'fontSize': '13px'}
    lbl_style = {
        'fontSize': '11px', 'fontWeight': '700', 'textTransform': 'uppercase',
        'letterSpacing': '1px', 'color': C['muted'], 'marginBottom': '4px',
        'display': 'block',
    }
    return html.Div([
        html.Div([
            html.Label('District', style=lbl_style),
            dcc.Dropdown(
                id='paps-district-filter',
                options=[{'label': 'All Districts', 'value': 'ALL'}] +
                        [{'label': d, 'value': d} for d in districts],
                value='ALL', clearable=False, style=dd_style,
            ),
        ]),
        html.Div([
            html.Label('Sector', style=lbl_style),
            dcc.Dropdown(
                id='paps-sector-filter',
                options=[{'label': 'All Sectors', 'value': 'ALL'}],
                value='ALL', clearable=False, style=dd_style,
            ),
        ]),
        html.Div([
            html.Label('Site', style=lbl_style),
            dcc.Dropdown(
                id='paps-site-filter',
                options=[{'label': 'All Sites', 'value': 'ALL'}],
                value='ALL', clearable=False, style=dd_style,
            ),
        ]),
    ], style={
        'display': 'flex', 'alignItems': 'flex-end', 'gap': '20px',
        'background': C['card'], 'padding': '16px 24px',
        'borderRadius': '10px',
        'boxShadow': '0 2px 8px rgba(13,33,55,0.05)',
        'marginBottom': '24px', 'width': 'fit-content',
    })


# ─────────────────────────────────────────────────────────────────────────────
# LAYOUT
# ─────────────────────────────────────────────────────────────────────────────

def layout():
    if PAPS.empty:
        return html.Div('PAPs_clean.csv not found.',
                        style={'padding': '40px 40px 40px 260px'})

    n         = len(PAPS)
    comp_rate = PAPS['compensation_received'].eq('Yes').mean() * 100
    sat_rate  = PAPS['compensation_satisfied'].eq('Yes').mean() * 100

    if comp_rate >= 90 and sat_rate >= 80:
        sc, st, sb = C['success'], '● ON TRACK', '#E8F5E9'
    elif comp_rate >= 70:
        sc, st, sb = C['warning'], '● ATTENTION REQUIRED', '#FFF3E0'
    else:
        sc, st, sb = C['danger'], '● CRITICAL', '#FFEBEE'

    return html.Div([

        # PAGE HEADER
        html.Div([
            html.Div([
                html.H2('Project Affected Persons', style={
                    'margin': '0 0 4px 0', 'fontWeight': '900',
                    'fontSize': '26px', 'color': C['primary'],
                }),
                html.P(
                    f'{n} PAPs interviewed across {PAPS["district"].nunique()} districts — IMCE Project Rwanda',
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
            dbc.Col(html.Div(id='kpi-total'), md=2),
            dbc.Col(html.Div(id='kpi-comp'),  md=2),
            dbc.Col(html.Div(id='kpi-sat'),   md=2),
            dbc.Col(html.Div(id='kpi-grm'),   md=2),
            dbc.Col(html.Div(id='kpi-multi'), md=2),
            dbc.Col(html.Div(id='kpi-risk'),  md=2),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 2 — Non-compensated table
        html.Div([card([
            section_title('⚠ Non-Compensated PAPs — Priority Cases',
                          'Detailed profile of PAPs who have not yet received compensation'),
            html.Div(id='paps-uncomp-table'),
        ])], style={'marginBottom': '24px'}),

        # SECTION 3 — Impact analysis
        dbc.Row([
            dbc.Col([card([
                section_title('Impact Type Distribution',
                              'Number of PAPs affected by each impact category'),
                dcc.Graph(id='paps-impact-types',
                          config={'displayModeBar': False}, style={'height': '280px'}),
            ])], md=5),
            dbc.Col([card([
                section_title('Impact Multiplicity & Compensation Rate',
                              'Compensation rate by number of impact types'),
                dcc.Graph(id='paps-impact-multiplicity',
                          config={'displayModeBar': False}, style={'height': '280px'}),
            ])], md=7),
        ], className='g-3', style={'marginBottom': '24px'}),

        dbc.Row([
            dbc.Col([card([
                section_title('Impact Combinations',
                              'Which types of impact most frequently occur together?'),
                dcc.Graph(id='paps-impact-heatmap',
                          config={'displayModeBar': False}, style={'height': '280px'}),
            ])], md=6),
            dbc.Col([card([
                section_title('Compensation Rate by District',
                              'Percentage of PAPs compensated in each district'),
                dcc.Graph(id='paps-comp-district',
                          config={'displayModeBar': False}, style={'height': '280px'}),
            ])], md=6),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 4 — Transparency
        dbc.Row([
            dbc.Col([card([
                section_title('Information & Transparency Funnel',
                              'At which stage do information gaps appear?'),
                dcc.Graph(id='paps-info-funnel',
                          config={'displayModeBar': False}, style={'height': '300px'}),
            ])], md=5),
            dbc.Col([card([
                section_title('Consultation Frequency',
                              'How often were PAPs consulted?'),
                dcc.Graph(id='paps-consultation',
                          config={'displayModeBar': False}, style={'height': '300px'}),
            ])], md=3),
            dbc.Col([card([
                section_title('SEA/SH Reporting Channel Awareness',
                              'Do PAPs know how to report SEA/SH?'),
                dcc.Graph(id='paps-sea',
                          config={'displayModeBar': False}, style={'height': '300px'}),
            ])], md=4),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 5 — GRM
        dbc.Row([
            dbc.Col([card([
                section_title('Grievance Process Funnel',
                              'From GRM awareness to full resolution'),
                dcc.Graph(id='paps-grm-funnel',
                          config={'displayModeBar': False}, style={'height': '310px'}),
            ])], md=4),
            dbc.Col([card([
                section_title('Grievance Channels Known to PAPs',
                              'Which channels are PAPs aware of?'),
                dcc.Graph(id='paps-grm-channels',
                          config={'displayModeBar': False}, style={'height': '310px'}),
            ])], md=4),
            dbc.Col([card([
                section_title('Resolution Outcomes',
                              'Among PAPs who submitted a grievance'),
                dcc.Graph(id='paps-grm-resolution',
                          config={'displayModeBar': False}, style={'height': '310px'}),
            ])], md=4),
        ], className='g-3', style={'marginBottom': '24px'}),

        dbc.Row([
            dbc.Col([card([
                section_title('Why Did PAPs Not Submit a Grievance?',
                              'Among non-submitters — satisfied or uninformed?'),
                dcc.Graph(id='paps-nonsubmit',
                          config={'displayModeBar': False}, style={'height': '260px'}),
            ])], md=6),
            dbc.Col([card([
                section_title('Response Time Reasonableness',
                              'Was the grievance response time acceptable?'),
                dcc.Graph(id='paps-response-time',
                          config={'displayModeBar': False}, style={'height': '260px'}),
            ])], md=3),
            dbc.Col([card([
                section_title('Grievance Channel Used',
                              'Which channel did PAPs actually use?'),
                dcc.Graph(id='paps-channel-used',
                          config={'displayModeBar': False}, style={'height': '260px'}),
            ])], md=3),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 6 — Satisfaction
        dbc.Row([
            dbc.Col([card([
                section_title('Satisfaction by Compensation Timing',
                              'PAPs compensated before construction are more satisfied'),
                dcc.Graph(id='paps-sat-timing',
                          config={'displayModeBar': False}, style={'height': '280px'}),
            ])], md=4),
            dbc.Col([card([
                section_title('Satisfaction by Number of Impacts',
                              'Does having more impacts affect satisfaction?'),
                dcc.Graph(id='paps-sat-impact',
                          config={'displayModeBar': False}, style={'height': '280px'}),
            ])], md=4),
            dbc.Col([card([
                section_title('Satisfaction by District',
                              'Which districts show the lowest satisfaction rates?'),
                dcc.Graph(id='paps-sat-district',
                          config={'displayModeBar': False}, style={'height': '280px'}),
            ])], md=4),
        ], className='g-3', style={'marginBottom': '24px'}),

        # SECTION 7 — Additional assistance
        dbc.Row([
            dbc.Col([card([
                section_title('Additional Assistance Provided',
                              'PAPs who received assistance beyond monetary compensation'),
                dcc.Graph(id='paps-assistance',
                          config={'displayModeBar': False}, style={'height': '260px'}),
            ])], md=5),
            dbc.Col([card([
                section_title('Compensation Timing Distribution',
                              'When did PAPs receive compensation?'),
                dcc.Graph(id='paps-comp-timing',
                          config={'displayModeBar': False}, style={'height': '260px'}),
            ])], md=3),
            dbc.Col([card([
                section_title('Risk Profile Summary',
                              'PAPs flagged with at least one vulnerability indicator'),
                html.Div(id='paps-risk-summary'),
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

    # ── CASCADE: sector options ───────────────────────────────────────────────
    @app.callback(
        Output('paps-sector-filter', 'options'),
        Output('paps-sector-filter', 'value'),
        Input('paps-district-filter', 'value'),
    )
    def update_sector_options(district):
        df = PAPS.copy()
        if district and district != 'ALL':
            df = df[df['district'] == district]
        sectors = sorted(df['sector'].dropna().unique().tolist())
        options = [{'label': 'All Sectors', 'value': 'ALL'}] + \
                  [{'label': s, 'value': s} for s in sectors]
        return options, 'ALL'

    # ── CASCADE: site options ─────────────────────────────────────────────────
    @app.callback(
        Output('paps-site-filter', 'options'),
        Output('paps-site-filter', 'value'),
        Input('paps-district-filter', 'value'),
        Input('paps-sector-filter', 'value'),
    )
    def update_site_options(district, sector):
        df = PAPS.copy()
        if district and district != 'ALL':
            df = df[df['district'] == district]
        if sector and sector != 'ALL':
            df = df[df['sector'] == sector]
        sites = sorted(df['site_name'].dropna().unique().tolist())
        options = [{'label': 'All Sites', 'value': 'ALL'}] + \
                  [{'label': s, 'value': s} for s in sites]
        return options, 'ALL'

    # ── KPIs ─────────────────────────────────────────────────────────────────
    @app.callback(
        Output('kpi-total', 'children'),
        Output('kpi-comp',  'children'),
        Output('kpi-sat',   'children'),
        Output('kpi-grm',   'children'),
        Output('kpi-multi', 'children'),
        Output('kpi-risk',  'children'),
        Input('paps-district-filter', 'value'),
        Input('paps-sector-filter',   'value'),
        Input('paps-site-filter',     'value'),
    )
    def update_kpis(district, sector, site):
        df = get_df(district, sector, site)
        if df.empty:
            return [html.Div('—')] * 6
        n        = len(df)
        comp_pct = df['compensation_received'].eq('Yes').mean() * 100
        sat_pct  = df['compensation_satisfied'].eq('Yes').mean() * 100
        grm_pct  = df['grm_aware'].eq('Yes').mean() * 100
        multi    = df['impact_count'].ge(2).sum()
        risk     = df['risk_flag'].sum()
        cc = C['success'] if comp_pct >= 90 else (C['warning'] if comp_pct >= 70 else C['danger'])
        sc = C['success'] if sat_pct  >= 80 else (C['warning'] if sat_pct  >= 60 else C['danger'])
        gc = C['success'] if grm_pct  >= 80 else C['warning']
        rc = C['danger']  if risk > 5 else (C['warning'] if risk > 0 else C['success'])
        return (
            kpi('PAPs Interviewed', str(n), f'{df["district"].nunique()} districts', C['accent']),
            kpi('Compensation Rate', f'{comp_pct:.0f}%',
                f'{df["compensation_received"].eq("Yes").sum()} of {n} compensated', cc),
            kpi('Satisfaction Rate', f'{sat_pct:.0f}%',
                f'{df["compensation_satisfied"].eq("Yes").sum()} satisfied', sc),
            kpi('GRM Awareness', f'{grm_pct:.0f}%',
                f'{df["grm_aware"].eq("Yes").sum()} aware of GRM', gc),
            kpi('Multi-Impact PAPs', str(multi), f'{multi} PAPs with 2+ impact types', C['p5']),
            kpi('PAPs at Risk', str(risk), 'Uncompensated, dissatisfied or unaware', rc),
        )

    # ── NON-COMPENSATED TABLE ─────────────────────────────────────────────────
    @app.callback(
        Output('paps-uncomp-table', 'children'),
        Input('paps-district-filter', 'value'),
        Input('paps-sector-filter',   'value'),
        Input('paps-site-filter',     'value'),
    )
    def update_uncomp_table(district, sector, site):
        df = get_df(district, sector, site)
        nc = df[df['compensation_received'] == 'No'].copy()
        if nc.empty:
            return html.Div([
                html.Span('✓', style={'fontSize': '28px', 'color': C['success']}),
                html.P('All PAPs in this selection have received compensation.',
                       style={'color': C['success'], 'fontWeight': '700',
                              'margin': '8px 0 0 0', 'fontSize': '14px'}),
            ], style={'textAlign': 'center', 'padding': '24px'})

        impact_labels = {
            'impact_loss_land': 'Land', 'impact_loss_house': 'House',
            'impact_loss_structure': 'Structure', 'impact_trees_crops': 'Trees/Crops',
        }

        def pill(text, ok_val):
            ok = text == ok_val
            return html.Span(text, style={
                'background': '#E8F5E9' if ok else '#FFEBEE',
                'color': C['success'] if ok else C['danger'],
                'padding': '3px 10px', 'borderRadius': '12px',
                'fontSize': '12px', 'fontWeight': '700',
            })

        rows = []
        for _, r in nc.iterrows():
            impacts = [lbl for col, lbl in impact_labels.items() if r.get(col, 0) == 1]
            griev   = r.get('grievance_submitted', 'No')
            sat     = r.get('compensation_satisfied', 'No')
            rows.append(html.Tr([
                html.Td(r.get('full_name', '—'),
                        style={'fontWeight': '700', 'fontSize': '13px', 'padding': '10px 12px'}),
                html.Td(r.get('district', '—'),
                        style={'fontSize': '13px', 'padding': '10px 12px'}),
                html.Td(r.get('site_name', '—'),
                        style={'fontSize': '12px', 'color': C['muted'], 'padding': '10px 12px'}),
                html.Td(html.Div([
                    html.Span(i, style={
                        'background': '#E3F2FD', 'color': C['accent'],
                        'padding': '2px 8px', 'borderRadius': '12px',
                        'fontSize': '11px', 'fontWeight': '700',
                        'marginRight': '4px', 'display': 'inline-block',
                    }) for i in impacts
                ] or [html.Span('Other', style={
                    'background': '#F3E5F5', 'color': C['p5'],
                    'padding': '2px 8px', 'borderRadius': '12px', 'fontSize': '11px',
                })]), style={'padding': '10px 12px'}),
                html.Td(r.get('compensation_missing_desc', '—'),
                        style={'fontSize': '12px', 'color': C['muted'], 'padding': '10px 12px',
                               'maxWidth': '320px', 'lineHeight': '1.5'}),
                html.Td(pill(griev, 'Yes'), style={'padding': '10px 12px', 'textAlign': 'center'}),
                html.Td(pill(sat,   'Yes'), style={'padding': '10px 12px', 'textAlign': 'center'}),
            ], style={
                'borderBottom': f'1px solid {C["border"]}',
                'background': '#FFFDE7' if griev == 'Yes' else 'white',
            }))

        return html.Table([
            html.Thead(html.Tr([
                html.Th(h, style={
                    'padding': '10px 12px', 'fontSize': '11px', 'fontWeight': '700',
                    'textTransform': 'uppercase', 'letterSpacing': '1px', 'color': C['muted'],
                    'background': C['light_bg'], 'borderBottom': f'2px solid {C["border"]}',
                }) for h in ['Name', 'District', 'Site', 'Impact Types',
                             'Reason', 'Grievance Submitted', 'Satisfied']
            ])),
            html.Tbody(rows),
        ], style={'width': '100%', 'borderCollapse': 'collapse', 'fontSize': '13px'})

    # ── IMPACT TYPES ─────────────────────────────────────────────────────────
    @app.callback(Output('paps-impact-types', 'figure'),
                  Input('paps-district-filter', 'value'),
                  Input('paps-sector-filter',   'value'),
                  Input('paps-site-filter',     'value'))
    def impact_types(district, sector, site):
        df = get_df(district, sector, site)
        if df.empty:
            return go.Figure()
        impact_map = {
            'impact_loss_land': 'Loss of Land', 'impact_loss_house': 'Loss of House',
            'impact_loss_structure': 'Loss of Structure',
            'impact_trees_crops': 'Trees & Crops', 'impact_other': 'Other',
        }
        labels = list(impact_map.values())
        vals   = [df[col].eq(1).sum() for col in impact_map]
        pcts   = [v / len(df) * 100 for v in vals]
        fig = go.Figure(go.Bar(
            y=labels, x=vals, orientation='h',
            marker_color=PALETTE[:len(labels)], marker_line_width=0,
            text=[f'{v} ({p:.0f}%)' for v, p in zip(vals, pcts)],
            textposition='outside', textfont=dict(size=12),
        ))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_xaxes(title='Number of PAPs', range=[0, max(vals) * 1.3 if vals else 10])
        return fig

    # ── IMPACT MULTIPLICITY — FIXED ───────────────────────────────────────────
    @app.callback(Output('paps-impact-multiplicity', 'figure'),
                  Input('paps-district-filter', 'value'),
                  Input('paps-sector-filter',   'value'),
                  Input('paps-site-filter',     'value'))
    def impact_multiplicity(district, sector, site):
        df = get_df(district, sector, site)
        if df.empty:
            return go.Figure()
        rows = []
        for n_imp in sorted(df['impact_count'].unique()):
            sub = df[df['impact_count'] == n_imp]
            rows.append({
                'impacts': str(n_imp),
                'count': len(sub),
                'comp_rate': sub['compensation_received'].eq('Yes').mean() * 100,
            })
        ddf = pd.DataFrame(rows)
        bar_colors = [
            C['success'] if r >= 80 else (C['warning'] if r >= 60 else C['danger'])
            for r in ddf['comp_rate']
        ]
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Number of PAPs', x=ddf['impacts'], y=ddf['count'],
            marker_color=C['accent'], marker_line_width=0,
            text=ddf['count'], textposition='outside',
            yaxis='y', offsetgroup=0,
        ))
        fig.add_trace(go.Scatter(
            name='Compensation Rate', x=ddf['impacts'], y=ddf['comp_rate'],
            mode='lines+markers+text',
            line=dict(color=C['secondary'], width=2.5),
            marker=dict(color=bar_colors, size=10, line=dict(color='white', width=2)),
            text=[f'{r:.0f}%' for r in ddf['comp_rate']],
            textposition='top center',
            textfont=dict(size=12, color=C['primary']),
            yaxis='y2',
        ))
        # FIX: xaxis and yaxis passed via update_xaxes/update_yaxes, NOT in update_layout
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Nunito, sans-serif', color=C['primary'], size=13),
            margin=dict(l=10, r=10, t=35, b=10),
            legend=dict(orientation='h', y=1.12, x=0, font=dict(size=12)),
            barmode='group',
            yaxis2=dict(
                title='Compensation Rate (%)', overlaying='y', side='right',
                range=[0, 115], ticksuffix='%',
                gridcolor='rgba(0,0,0,0)', linecolor=C['border'],
                tickfont=dict(size=12),
            ),
            hoverlabel=dict(bgcolor=C['primary'], bordercolor=C['border'],
                            font=dict(family='Nunito, sans-serif', size=13, color='#FFFFFF')),
        )
        fig.update_xaxes(title='Number of Impact Types', tickfont=dict(size=12),
                         gridcolor=C['border'], linecolor=C['border'])
        fig.update_yaxes(title='Number of PAPs', gridcolor=C['border'],
                         linecolor=C['border'], tickfont=dict(size=12))
        return fig

    # ── IMPACT HEATMAP ────────────────────────────────────────────────────────
    @app.callback(Output('paps-impact-heatmap', 'figure'),
                  Input('paps-district-filter', 'value'),
                  Input('paps-sector-filter',   'value'),
                  Input('paps-site-filter',     'value'))
    def impact_heatmap(district, sector, site):
        df = get_df(district, sector, site)
        if df.empty:
            return go.Figure()
        impact_map = {
            'impact_loss_land': 'Land', 'impact_loss_house': 'House',
            'impact_loss_structure': 'Structure', 'impact_trees_crops': 'Trees/Crops',
        }
        cols   = list(impact_map.keys())
        labels = list(impact_map.values())
        n      = len(cols)
        matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                matrix[i][j] = df[cols[i]].sum() if i == j else \
                    ((df[cols[i]] == 1) & (df[cols[j]] == 1)).sum()
        fig = go.Figure(go.Heatmap(
            z=matrix, x=labels, y=labels,
            colorscale=[[0, '#EFF8F7'], [0.5, '#00BFA5'], [1, '#0D2137']],
            text=matrix.astype(int), texttemplate='%{text}',
            textfont=dict(size=14, color='white'), showscale=False,
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Nunito, sans-serif', color=C['primary'], size=13),
            margin=dict(l=10, r=10, t=10, b=10),
        )
        return fig

    # ── COMP BY DISTRICT ──────────────────────────────────────────────────────
    @app.callback(Output('paps-comp-district', 'figure'),
                  Input('paps-district-filter', 'value'),
                  Input('paps-sector-filter',   'value'),
                  Input('paps-site-filter',     'value'))
    def comp_by_district(district, sector, site):
        df = get_df(district, sector, site)
        if df.empty:
            return go.Figure()
        data = df.groupby('district').apply(
            lambda x: pd.Series({
                'comp_rate': x['compensation_received'].eq('Yes').mean() * 100,
                'count': len(x),
            })
        ).reset_index().sort_values('comp_rate')
        colors = [C['success'] if r >= 90 else (C['warning'] if r >= 70 else C['danger'])
                  for r in data['comp_rate']]
        fig = go.Figure(go.Bar(
            y=data['district'], x=data['comp_rate'], orientation='h',
            marker_color=colors, marker_line_width=0,
            text=[f'{r:.0f}% (n={int(c)})' for r, c in zip(data['comp_rate'], data['count'])],
            textposition='outside', textfont=dict(size=12),
        ))
        fig.add_vline(x=80, line_dash='dot', line_color=C['muted'],
                      annotation_text='80% target',
                      annotation_font=dict(size=11, color=C['muted']))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_xaxes(range=[0, 120], ticksuffix='%', title='Compensation Rate')
        return fig

    # ── INFO FUNNEL ───────────────────────────────────────────────────────────
    @app.callback(Output('paps-info-funnel', 'figure'),
                  Input('paps-district-filter', 'value'),
                  Input('paps-sector-filter',   'value'),
                  Input('paps-site-filter',     'value'))
    def info_funnel(district, sector, site):
        df = get_df(district, sector, site)
        if df.empty:
            return go.Figure()
        steps = [
            ('Informed Before Project', df['informed_before_project'].eq('Yes').sum()),
            ('Clear on Activities',     df['info_clear_activities'].eq('Yes').sum()),
            ('Clear on Impacts',        df['info_clear_impacts'].eq('Yes').sum()),
            ('Clear on Rights',         df['info_clear_rights'].eq('Yes').sum()),
            ('Valuation Explained',     df['valuation_explained'].eq('Yes').sum()),
            ('Aware of GRM',            df['grm_aware'].eq('Yes').sum()),
        ]
        labels, vals = zip(*steps)
        fig = go.Figure(go.Funnel(
            y=list(labels), x=list(vals),
            textinfo='value+percent initial',
            marker_color=[C['accent'], C['p2'], C['p3'], C['p2'], C['p3'], C['p5']],
            connector=dict(line=dict(color=C['border'], width=1.5)),
            textfont=dict(family='Nunito, sans-serif', size=12),
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Nunito, sans-serif', color=C['primary'], size=13),
            margin=dict(l=10, r=60, t=10, b=10), showlegend=False,
        )
        return fig

    # ── CONSULTATION ──────────────────────────────────────────────────────────
    @app.callback(Output('paps-consultation', 'figure'),
                  Input('paps-district-filter', 'value'),
                  Input('paps-sector-filter',   'value'),
                  Input('paps-site-filter',     'value'))
    def consultation(district, sector, site):
        df = get_df(district, sector, site)
        if df.empty:
            return go.Figure()
        counts = df['consultation_frequency'].value_counts()
        fig = go.Figure(go.Pie(
            labels=counts.index, values=counts.values, hole=0.55,
            marker_colors=[C['success'], C['p3'], C['danger']],
            textinfo='label+percent',
            textfont=dict(size=12, family='Nunito, sans-serif'), showlegend=False,
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Nunito, sans-serif', size=13),
            margin=dict(l=10, r=10, t=10, b=10),
        )
        return fig

    # ── SEA CHANNEL ───────────────────────────────────────────────────────────
    @app.callback(Output('paps-sea', 'figure'),
                  Input('paps-district-filter', 'value'),
                  Input('paps-sector-filter',   'value'),
                  Input('paps-site-filter',     'value'))
    def sea_channel(district, sector, site):
        df = get_df(district, sector, site)
        if df.empty:
            return go.Figure()
        counts = df['sea_sh_channel'].value_counts()
        color_map = {'Yes': C['success'], 'No': C['danger'], "Don't know": C['warning']}
        colors = [color_map.get(l, C['muted']) for l in counts.index]
        fig = go.Figure(go.Pie(
            labels=counts.index, values=counts.values, hole=0.55,
            marker_colors=colors, textinfo='label+percent',
            textfont=dict(size=12, family='Nunito, sans-serif'), showlegend=False,
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Nunito, sans-serif', size=13),
            margin=dict(l=10, r=10, t=10, b=10),
        )
        return fig

    # ── GRM FUNNEL ────────────────────────────────────────────────────────────
    @app.callback(Output('paps-grm-funnel', 'figure'),
                  Input('paps-district-filter', 'value'),
                  Input('paps-sector-filter',   'value'),
                  Input('paps-site-filter',     'value'))
    def grm_funnel(district, sector, site):
        df = get_df(district, sector, site)
        if df.empty:
            return go.Figure()
        n         = len(df)
        aware     = df['grm_aware'].eq('Yes').sum()
        submitted = df['grievance_submitted'].eq('Yes').sum()
        resolved  = df['grievance_resolved'].eq('Fully resolved').sum()
        fig = go.Figure(go.Funnel(
            y=['PAPs Total', 'Aware of GRM', 'Submitted Grievance', 'Fully Resolved'],
            x=[n, aware, submitted, resolved],
            textinfo='value+percent initial',
            marker_color=[C['accent'], C['p2'], C['p3'], C['success']],
            connector=dict(line=dict(color=C['border'], width=1.5)),
            textfont=dict(family='Nunito, sans-serif', size=12),
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Nunito, sans-serif', color=C['primary'], size=13),
            margin=dict(l=10, r=70, t=10, b=10), showlegend=False,
        )
        return fig

    # ── GRM CHANNELS ─────────────────────────────────────────────────────────
    @app.callback(Output('paps-grm-channels', 'figure'),
                  Input('paps-district-filter', 'value'),
                  Input('paps-sector-filter',   'value'),
                  Input('paps-site-filter',     'value'))
    def grm_channels(district, sector, site):
        df = get_df(district, sector, site)
        if df.empty:
            return go.Figure()
        channel_map = {
            'grm_channel_grc':      'Grievance Redress Committee',
            'grm_channel_cell':     'Cell Administration',
            'grm_channel_sector':   'Sector Administration',
            'grm_channel_district': 'District Office',
            'grm_channel_other':    'Other',
        }
        n = len(df)
        labels, vals = [], []
        for col, lbl in channel_map.items():
            if col in df.columns:
                labels.append(lbl)
                vals.append(df[col].sum())
        pcts = [v / n * 100 for v in vals]
        fig = go.Figure(go.Bar(
            y=labels, x=pcts, orientation='h',
            marker_color=PALETTE[:len(labels)], marker_line_width=0,
            text=[f'{p:.0f}% ({v})' for p, v in zip(pcts, vals)],
            textposition='outside', textfont=dict(size=12),
        ))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_xaxes(range=[0, 120], ticksuffix='%', title='% of PAPs Aware')
        return fig

    # ── GRM RESOLUTION ────────────────────────────────────────────────────────
    @app.callback(Output('paps-grm-resolution', 'figure'),
                  Input('paps-district-filter', 'value'),
                  Input('paps-sector-filter',   'value'),
                  Input('paps-site-filter',     'value'))
    def grm_resolution(district, sector, site):
        df = get_df(district, sector, site)
        if df.empty:
            return go.Figure()
        sub    = df[df['grievance_submitted'] == 'Yes']
        counts = sub['grievance_resolved'].value_counts(dropna=False)
        counts.index = counts.index.fillna('No Response')
        color_map = {
            'Fully resolved': C['success'], 'Partially resolved': C['warning'],
            'Not resolved': C['danger'],    'No Response': C['muted'],
        }
        colors = [color_map.get(l, C['muted']) for l in counts.index]
        fig = go.Figure(go.Pie(
            labels=counts.index, values=counts.values, hole=0.55,
            marker_colors=colors, textinfo='label+value',
            textfont=dict(size=12, family='Nunito, sans-serif'), showlegend=False,
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Nunito, sans-serif', size=13),
            margin=dict(l=10, r=10, t=10, b=10),
        )
        return fig

    # ── NON-SUBMITTERS ────────────────────────────────────────────────────────
    @app.callback(Output('paps-nonsubmit', 'figure'),
                  Input('paps-district-filter', 'value'),
                  Input('paps-sector-filter',   'value'),
                  Input('paps-site-filter',     'value'))
    def non_submitters(district, sector, site):
        df = get_df(district, sector, site)
        if df.empty:
            return go.Figure()
        ns   = df[df['grievance_submitted'] == 'No']
        cats = {
            'Satisfied & GRM Aware':  ((ns['compensation_satisfied'] == 'Yes') & (ns['grm_aware'] == 'Yes')).sum(),
            'Satisfied but Unaware':  ((ns['compensation_satisfied'] == 'Yes') & (ns['grm_aware'] == 'No')).sum(),
            'Dissatisfied but Aware': ((ns['compensation_satisfied'] == 'No')  & (ns['grm_aware'] == 'Yes')).sum(),
            'Dissatisfied & Unaware': ((ns['compensation_satisfied'] == 'No')  & (ns['grm_aware'] == 'No')).sum(),
        }
        fig = go.Figure(go.Bar(
            x=list(cats.keys()), y=list(cats.values()),
            marker_color=[C['success'], C['warning'], C['danger'], C['p4']],
            marker_line_width=0,
            text=list(cats.values()), textposition='outside', textfont=dict(size=13),
        ))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_xaxes(tickangle=-15)
        fig.update_yaxes(title='Number of PAPs')
        return fig

    # ── RESPONSE TIME ─────────────────────────────────────────────────────────
    @app.callback(Output('paps-response-time', 'figure'),
                  Input('paps-district-filter', 'value'),
                  Input('paps-sector-filter',   'value'),
                  Input('paps-site-filter',     'value'))
    def response_time(district, sector, site):
        df = get_df(district, sector, site)
        if df.empty:
            return go.Figure()
        sub    = df[df['grievance_submitted'] == 'Yes']
        counts = sub['response_time_reasonable'].value_counts(dropna=False)
        counts.index = counts.index.fillna('N/A')
        color_map = {'Yes': C['success'], 'No': C['danger'], 'N/A': C['muted']}
        colors = [color_map.get(l, C['muted']) for l in counts.index]
        fig = go.Figure(go.Pie(
            labels=counts.index, values=counts.values, hole=0.55,
            marker_colors=colors, textinfo='label+value',
            textfont=dict(size=12, family='Nunito, sans-serif'), showlegend=False,
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Nunito, sans-serif', size=13),
            margin=dict(l=10, r=10, t=10, b=10),
        )
        return fig

    # ── CHANNEL USED ──────────────────────────────────────────────────────────
    @app.callback(Output('paps-channel-used', 'figure'),
                  Input('paps-district-filter', 'value'),
                  Input('paps-sector-filter',   'value'),
                  Input('paps-site-filter',     'value'))
    def channel_used(district, sector, site):
        df = get_df(district, sector, site)
        if df.empty:
            return go.Figure()
        sub = df[df['grievance_submitted'] == 'Yes']

        def simplify(ch):
            ch = str(ch)
            if 'Grievance Redress' in ch or 'GRC' in ch:
                return 'GRC'
            elif 'Cell' in ch:
                return 'Cell Admin'
            elif 'District' in ch:
                return 'District'
            elif 'Sector' in ch:
                return 'Sector'
            return 'Other'

        channels = sub['grievance_channel'].apply(simplify).value_counts()
        fig = go.Figure(go.Pie(
            labels=channels.index, values=channels.values, hole=0.55,
            marker_colors=PALETTE[:len(channels)], textinfo='label+value',
            textfont=dict(size=12, family='Nunito, sans-serif'), showlegend=False,
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Nunito, sans-serif', size=13),
            margin=dict(l=10, r=10, t=10, b=10),
        )
        return fig

    # ── SATISFACTION BY TIMING ────────────────────────────────────────────────
    @app.callback(Output('paps-sat-timing', 'figure'),
                  Input('paps-district-filter', 'value'),
                  Input('paps-sector-filter',   'value'),
                  Input('paps-site-filter',     'value'))
    def sat_by_timing(district, sector, site):
        df = get_df(district, sector, site)
        if df.empty:
            return go.Figure()
        data = df.groupby('compensation_timing').apply(
            lambda x: pd.Series({
                'sat_rate': x['compensation_satisfied'].eq('Yes').mean() * 100,
                'count': len(x),
            })
        ).reset_index()
        colors = [C['success'] if r >= 80 else (C['warning'] if r >= 60 else C['danger'])
                  for r in data['sat_rate']]
        fig = go.Figure(go.Bar(
            x=data['compensation_timing'], y=data['sat_rate'],
            marker_color=colors, marker_line_width=0,
            text=[f'{r:.0f}% (n={int(c)})' for r, c in zip(data['sat_rate'], data['count'])],
            textposition='outside', textfont=dict(size=12),
        ))
        fig.add_hline(y=80, line_dash='dot', line_color=C['muted'],
                      annotation_text='80% target', annotation_font_size=11)
        fig.update_layout(**BASE_LAYOUT)
        fig.update_xaxes(tickangle=-15)
        fig.update_yaxes(title='Satisfaction Rate (%)', ticksuffix='%', range=[0, 115])
        return fig

    # ── SATISFACTION BY IMPACT ────────────────────────────────────────────────
    @app.callback(Output('paps-sat-impact', 'figure'),
                  Input('paps-district-filter', 'value'),
                  Input('paps-sector-filter',   'value'),
                  Input('paps-site-filter',     'value'))
    def sat_by_impact(district, sector, site):
        df = get_df(district, sector, site)
        if df.empty:
            return go.Figure()
        data = df.groupby('impact_count').apply(
            lambda x: pd.Series({
                'sat_rate': x['compensation_satisfied'].eq('Yes').mean() * 100,
                'count': len(x),
            })
        ).reset_index()
        fig = go.Figure(go.Bar(
            x=data['impact_count'].astype(str), y=data['sat_rate'],
            marker_color=C['p5'], marker_line_width=0,
            text=[f'{r:.0f}% (n={int(c)})' for r, c in zip(data['sat_rate'], data['count'])],
            textposition='outside', textfont=dict(size=12),
        ))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_xaxes(title='Number of Impact Types')
        fig.update_yaxes(title='Satisfaction Rate (%)', ticksuffix='%', range=[0, 115])
        return fig

    # ── SATISFACTION BY DISTRICT ───────────────────────────────────────────────
    @app.callback(Output('paps-sat-district', 'figure'),
                  Input('paps-district-filter', 'value'),
                  Input('paps-sector-filter',   'value'),
                  Input('paps-site-filter',     'value'))
    def sat_by_district(district, sector, site):
        df = get_df(district, sector, site)
        if df.empty:
            return go.Figure()
        data = df.groupby('district').apply(
            lambda x: pd.Series({
                'sat_rate': x['compensation_satisfied'].eq('Yes').mean() * 100,
                'count': len(x),
            })
        ).reset_index().sort_values('sat_rate')
        colors = [C['success'] if r >= 80 else (C['warning'] if r >= 60 else C['danger'])
                  for r in data['sat_rate']]
        fig = go.Figure(go.Bar(
            y=data['district'], x=data['sat_rate'], orientation='h',
            marker_color=colors, marker_line_width=0,
            text=[f'{r:.0f}% (n={int(c)})' for r, c in zip(data['sat_rate'], data['count'])],
            textposition='outside', textfont=dict(size=12),
        ))
        fig.add_vline(x=80, line_dash='dot', line_color=C['muted'],
                      annotation_text='80%', annotation_font_size=11)
        fig.update_layout(**BASE_LAYOUT)
        fig.update_xaxes(range=[0, 120], ticksuffix='%', title='Satisfaction Rate')
        return fig

    # ── ADDITIONAL ASSISTANCE ────────────────────────────────────────────────
    @app.callback(Output('paps-assistance', 'figure'),
                  Input('paps-district-filter', 'value'),
                  Input('paps-sector-filter',   'value'),
                  Input('paps-site-filter',     'value'))
    def assistance(district, sector, site):
        df = get_df(district, sector, site)
        if df.empty:
            return go.Figure()
        dist_data = df.groupby('district')['additional_assistance'].apply(
            lambda x: x.eq('Yes').sum()
        ).reset_index()
        dist_data.columns = ['district', 'with_assistance']
        dist_data = dist_data[dist_data['with_assistance'] > 0].sort_values('with_assistance', ascending=False)
        if dist_data.empty:
            return go.Figure()
        fig = go.Figure(go.Bar(
            x=dist_data['district'], y=dist_data['with_assistance'],
            marker_color=C['secondary'], marker_line_width=0,
            text=dist_data['with_assistance'],
            textposition='outside', textfont=dict(size=13),
        ))
        fig.update_layout(**BASE_LAYOUT)
        fig.update_yaxes(title='PAPs with Additional Assistance')
        return fig

    # ── COMP TIMING ───────────────────────────────────────────────────────────
    @app.callback(Output('paps-comp-timing', 'figure'),
                  Input('paps-district-filter', 'value'),
                  Input('paps-sector-filter',   'value'),
                  Input('paps-site-filter',     'value'))
    def comp_timing(district, sector, site):
        df = get_df(district, sector, site)
        if df.empty:
            return go.Figure()
        counts = df['compensation_timing'].value_counts()
        color_map = {
            'Before construction': C['success'],
            'During construction': C['warning'],
            'Have not received compensation': C['danger'],
        }
        colors = [color_map.get(l, C['muted']) for l in counts.index]
        fig = go.Figure(go.Pie(
            labels=counts.index, values=counts.values, hole=0.55,
            marker_colors=colors, textinfo='label+value',
            textfont=dict(size=12, family='Nunito, sans-serif'), showlegend=False,
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Nunito, sans-serif', size=13),
            margin=dict(l=10, r=10, t=10, b=10),
        )
        return fig

    # ── RISK SUMMARY ──────────────────────────────────────────────────────────
    @app.callback(Output('paps-risk-summary', 'children'),
                  Input('paps-district-filter', 'value'),
                  Input('paps-sector-filter',   'value'),
                  Input('paps-site-filter',     'value'))
    def risk_summary(district, sector, site):
        df = get_df(district, sector, site)
        if df.empty:
            return html.Div('—')
        n = len(df)
        indicators = [
            ('Not Compensated',      df['compensation_received'].eq('No').sum()),
            ('Dissatisfied',         df['compensation_satisfied'].eq('No').sum()),
            ('Unaware of GRM',       df['grm_aware'].eq('No').sum()),
            ('Grievance Unresolved', df['grievance_resolved'].eq('Not resolved').sum()),
            ('Consulted Only Once',  df['consultation_frequency'].eq('Once').sum()),
            ('SEA Channel Unknown',  df['sea_sh_channel'].eq("Don't know").sum()),
        ]
        items = []
        for label, count in indicators:
            pct   = count / n * 100
            color = C['success'] if count == 0 else (C['warning'] if pct < 20 else C['danger'])
            items.append(html.Div([
                html.Div([
                    html.Span(label, style={
                        'fontSize': '13px', 'fontWeight': '600', 'color': C['primary'],
                    }),
                    html.Span(f'{count} PAPs', style={
                        'fontSize': '13px', 'fontWeight': '800', 'color': color,
                    }),
                ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '4px'}),
                html.Div([
                    html.Div(style={
                        'width': f'{min(pct, 100):.1f}%', 'height': '5px',
                        'background': color, 'borderRadius': '3px',
                    }),
                ], style={'background': C['border'], 'borderRadius': '3px', 'overflow': 'hidden'}),
            ], style={'marginBottom': '13px'}))
        return html.Div(items)