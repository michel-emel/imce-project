"""
IMCE Dashboard — Executive Summary
360° project view for World Bank decision-makers.
6 datasets synthesized into KPIs, alerts, and dataset cards.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash import dcc, html
import dash_bootstrap_components as dbc
import os

# ─────────────────────────────────────────────────────────────────────────────
# DESIGN TOKENS
# ─────────────────────────────────────────────────────────────────────────────

C = {
    'primary':    '#0D2137',
    'secondary':  '#00BFA5',
    'accent':     '#1565C0',
    'success':    '#2E7D32',
    'success_bg': '#E8F5E9',
    'warning':    '#E65100',
    'warning_bg': '#FFF3E0',
    'danger':     '#B71C1C',
    'danger_bg':  '#FFEBEE',
    'light_bg':   '#F0F4F8',
    'card':       '#FFFFFF',
    'muted':      '#607D8B',
    'border':     '#E0E8F0',
    'p1': '#1565C0', 'p2': '#00BFA5', 'p3': '#FFA726',
    'p4': '#EF5350', 'p5': '#AB47BC', 'p6': '#26A69A',
}

BASE_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Nunito, sans-serif', color=C['primary'], size=12),
    margin=dict(l=10, r=10, t=25, b=10),
    hoverlabel=dict(bgcolor=C['primary'], bordercolor=C['border'],
                    font=dict(family='Nunito, sans-serif', size=12)),
    xaxis=dict(gridcolor=C['border'], linecolor=C['border']),
    yaxis=dict(gridcolor=C['border'], linecolor=C['border']),
)

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────

def _path(filename):
    base = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(base, filename)


def load_all():
    paps        = pd.read_csv(_path('PAPs_clean.csv'))
    workers     = pd.read_csv(_path('workers_clean.csv'))
    contractors = pd.read_csv(_path('contractors_clean.csv'))
    grc         = pd.read_csv(_path('GRC_clean.csv'))
    district    = pd.read_csv(_path('district_clean.csv'))
    checklist   = pd.read_csv(_path('checklist_clean.csv'))
    return paps, workers, contractors, grc, district, checklist


PAPS, WORKERS, CONTRACTORS, GRC, DISTRICT, CHECKLIST = load_all()

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


def sec_title(title, subtitle=None):
    return html.Div([
        html.H5(title, style={'margin': '0 0 2px 0', 'fontWeight': '700',
                              'fontSize': '15px', 'color': C['primary']}),
        html.P(subtitle, style={'margin': '0', 'fontSize': '12px', 'color': C['muted']})
        if subtitle else html.Span(),
    ], style={'marginBottom': '14px', 'paddingBottom': '10px',
              'borderBottom': f'2px solid {C["border"]}'})


def kpi_card(icon, title, value, sub, color, alert=False):
    bg = C['danger_bg'] if alert else C['card']
    border_color = C['danger'] if alert else color
    return html.Div([
        html.Div([
            html.Span(icon, style={'fontSize': '22px', 'marginRight': '10px'}),
            html.Span(title, style={'fontSize': '11px', 'fontWeight': '700',
                                    'textTransform': 'uppercase',
                                    'letterSpacing': '1.1px', 'color': C['muted']}),
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}),
        html.H2(str(value), style={
            'margin': '0 0 4px 0', 'fontSize': '32px',
            'fontWeight': '900', 'color': border_color, 'lineHeight': '1',
        }),
        html.P(str(sub), style={'margin': '0', 'fontSize': '12px', 'color': C['muted']}),
    ], style={
        'background': bg, 'borderRadius': '12px', 'padding': '18px 20px',
        'boxShadow': '0 2px 8px rgba(13,33,55,0.07)',
        'borderTop': f'4px solid {border_color}',
    })


def alert_row(icon, text, color, bg):
    return html.Div([
        html.Span(icon + ' ', style={'fontSize': '15px'}),
        html.Span(text, style={'fontSize': '13px', 'fontWeight': '700', 'color': color}),
    ], style={
        'background': bg, 'border': f'1px solid {color}',
        'borderRadius': '8px', 'padding': '9px 16px', 'marginBottom': '8px',
    })


def mini_prog(label, pct, color):
    return html.Div([
        html.Div([
            html.Span(label, style={'fontSize': '12px', 'color': C['muted'],
                                    'flex': '1'}),
            html.Span(f'{pct:.0f}%', style={'fontSize': '12px',
                                            'fontWeight': '800', 'color': color}),
        ], style={'display': 'flex', 'marginBottom': '4px'}),
        html.Div(html.Div(style={
            'width': f'{min(pct, 100):.0f}%', 'height': '5px',
            'background': color, 'borderRadius': '3px',
        }), style={
            'background': C['border'], 'borderRadius': '3px',
            'marginBottom': '10px', 'overflow': 'hidden',
        }),
    ])


def dataset_card(icon, title, color, metrics, link_href, status_text, status_color):
    return html.Div([
        # Header
        html.Div([
            html.Div([
                html.Span(icon, style={'fontSize': '20px', 'marginRight': '10px'}),
                html.Span(title, style={
                    'fontSize': '14px', 'fontWeight': '800', 'color': C['primary'],
                }),
            ], style={'display': 'flex', 'alignItems': 'center'}),
            html.Span(status_text, style={
                'background': status_color + '20',
                'color': status_color,
                'padding': '3px 10px', 'borderRadius': '10px',
                'fontSize': '11px', 'fontWeight': '800',
                'border': f'1px solid {status_color}',
            }),
        ], style={
            'display': 'flex', 'justifyContent': 'space-between',
            'alignItems': 'center', 'marginBottom': '14px',
            'paddingBottom': '10px', 'borderBottom': f'2px solid {C["border"]}',
        }),
        # Metrics
        html.Div(metrics, style={'marginBottom': '14px'}),
        # Link
        html.A(f'→ View full {title} analysis',
               href=link_href,
               style={
                   'fontSize': '12px', 'color': color,
                   'fontWeight': '700', 'textDecoration': 'none',
               }),
    ], style={
        'background': C['card'], 'borderRadius': '12px',
        'padding': '18px 20px', 'height': '100%',
        'boxShadow': '0 2px 8px rgba(13,33,55,0.07)',
        'borderLeft': f'4px solid {color}',
    })


# ─────────────────────────────────────────────────────────────────────────────
# COMPUTED METRICS
# ─────────────────────────────────────────────────────────────────────────────

def compute_metrics():
    # PAPs
    paps_total = len(PAPS)
    paps_comp  = int((PAPS['compensation_received'] == 'Yes').sum())
    paps_comp_pct = paps_comp / paps_total * 100
    paps_grm_aware = int((PAPS['grm_aware'] == 'Yes').sum())
    paps_grievance = int((PAPS['grievance_submitted'] == 'Yes').sum())
    paps_resolved  = int((PAPS['grievance_resolved'] == 'Fully resolved').sum())
    paps_unsat     = int((PAPS['compensation_satisfied'] == 'No').sum())

    # Workers
    w_total   = len(WORKERS)
    w_female  = int((WORKERS['gender'] == 'Female').sum())
    w_female_pct = w_female / w_total * 100
    w_trained = int((WORKERS['training_count'] > 0).sum())
    w_trained_pct = w_trained / w_total * 100

    # Contractors
    c_total    = len(CONTRACTORS)
    c_incident = int((CONTRACTORS['incidents_occurred'] == 'Yes').sum())
    c_incident_pct = c_incident / c_total * 100
    c_avg_women = float(CONTRACTORS['women_percent'].mean())
    c_avg_local = float(CONTRACTORS['local_percent'].mean())

    # GRC
    g_total     = len(GRC)
    g_complaints = int(GRC['complaints_received'].sum())
    g_resolved   = int(GRC['complaints_resolved'].sum())
    g_pending    = int(GRC['complaints_pending'].sum())
    g_res_rate   = g_resolved / g_complaints * 100 if g_complaints > 0 else 0

    # District
    d_total      = len(DISTRICT)
    d_hh         = int(DISTRICT['households_affected'].sum())
    d_pending    = int(DISTRICT['not_yet_compensated_count'].sum())
    # weighted compensation rate
    d_comp_rate  = sum(
        r['compensation_progress'] * r['households_affected']
        for _, r in DISTRICT.iterrows()
        if pd.notna(r['compensation_progress']) and pd.notna(r['households_affected'])
    ) / d_hh if d_hh > 0 else 0

    # Checklist
    chk_comply = 100.0
    chk_comp_pct = float(CHECKLIST.iloc[0]['compensation_progress_pct'])

    return dict(
        paps_total=paps_total, paps_comp=paps_comp, paps_comp_pct=paps_comp_pct,
        paps_grm_aware=paps_grm_aware, paps_grievance=paps_grievance,
        paps_resolved=paps_resolved, paps_unsat=paps_unsat,
        w_total=w_total, w_female=w_female, w_female_pct=w_female_pct,
        w_trained=w_trained, w_trained_pct=w_trained_pct,
        c_total=c_total, c_incident=c_incident, c_incident_pct=c_incident_pct,
        c_avg_women=c_avg_women, c_avg_local=c_avg_local,
        g_total=g_total, g_complaints=g_complaints, g_resolved=g_resolved,
        g_pending=g_pending, g_res_rate=g_res_rate,
        d_total=d_total, d_hh=d_hh, d_pending=d_pending, d_comp_rate=d_comp_rate,
        chk_comply=chk_comply, chk_comp_pct=chk_comp_pct,
    )


M = compute_metrics()


# ─────────────────────────────────────────────────────────────────────────────
# FIGURES
# ─────────────────────────────────────────────────────────────────────────────

def _radar_fig():
    """Project health radar across 6 dimensions."""
    categories = [
        'PAP Compensation', 'Worker Safety',
        'Contractor Compliance', 'GRC Resolution',
        'District Progress', 'Site Audit',
    ]
    values = [
        M['paps_comp_pct'],
        M['w_trained_pct'],
        100 - M['c_incident_pct'],   # inverse: lower incidents = higher score
        M['g_res_rate'],
        min(M['d_comp_rate'], 100),
        M['chk_comply'],
    ]
    # Close the radar loop
    cats  = categories + [categories[0]]
    vals  = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals, theta=cats, fill='toself',
        fillcolor='rgba(21, 101, 192, 0.15)',
        line=dict(color=C['accent'], width=2),
        marker=dict(color=C['accent'], size=7),
        name='Project Score',
        hovertemplate='<b>%{theta}</b><br>Score: %{r:.0f}%<extra></extra>',
    ))
    # Target line at 80%
    target_val = [80] * len(cats)
    fig.add_trace(go.Scatterpolar(
        r=target_val, theta=cats, fill='none',
        line=dict(color=C['secondary'], width=1.5, dash='dot'),
        name='80% Target',
        hoverinfo='skip',
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(
                visible=True, range=[0, 100],
                ticksuffix='%', tickfont=dict(size=9, color=C['muted']),
                gridcolor=C['border'], linecolor=C['border'],
            ),
            angularaxis=dict(
                tickfont=dict(size=11, family='Nunito, sans-serif'),
                gridcolor=C['border'], linecolor=C['border'],
            ),
        ),
        legend=dict(
            font=dict(size=11), bgcolor='rgba(255,255,255,0.9)',
            bordercolor=C['border'], borderwidth=1,
        ),
        margin=dict(l=50, r=50, t=30, b=30),
        font=dict(family='Nunito, sans-serif'),
    )
    return fig


def _timeline_fig():
    """Interview dates across datasets — project monitoring coverage."""
    date_data = []
    for df, label, color in [
        (PAPS,        'PAPs',        C['p1']),
        (WORKERS,     'Workers',     C['p2']),
        (CONTRACTORS, 'Contractors', C['p3']),
        (GRC,         'GRC',         C['p5']),
        (DISTRICT,    'District',    C['p6']),
    ]:
        date_col = 'date_interview' if 'date_interview' in df.columns else 'date_visit'
        if date_col in df.columns:
            dates = pd.to_datetime(df[date_col], errors='coerce').dropna()
            date_data.append((dates, label, color))

    fig = go.Figure()
    for i, (dates, label, color) in enumerate(date_data):
        counts = dates.dt.strftime('%Y-%m-%d').value_counts().sort_index()
        fig.add_trace(go.Scatter(
            x=counts.index, y=[i + 1] * len(counts),
            mode='markers',
            marker=dict(color=color, size=counts.values * 3 + 6,
                        opacity=0.75, line=dict(color='white', width=1)),
            name=label,
            hovertemplate=f'<b>{label}</b><br>Date: %{{x}}<br>Surveys: %{{text}}<extra></extra>',
            text=counts.values,
        ))
    fig.update_layout(**BASE_LAYOUT)
    fig.update_xaxes(title='Survey Date', tickangle=-30)
    fig.update_yaxes(
        tickvals=list(range(1, 6)),
        ticktext=['PAPs', 'Workers', 'Contractors', 'GRC', 'District'],
        title='',
    )
    return fig


def _project_score_gauge():
    """Single overall project health score."""
    weights = [0.30, 0.15, 0.15, 0.15, 0.15, 0.10]
    dims    = [
        M['paps_comp_pct'],
        M['w_trained_pct'],
        100 - M['c_incident_pct'],
        M['g_res_rate'],
        min(M['d_comp_rate'], 100),
        M['chk_comply'],
    ]
    score = sum(w * d for w, d in zip(weights, dims))
    color = C['success'] if score >= 75 else (C['warning'] if score >= 55 else C['danger'])

    fig = go.Figure(go.Indicator(
        mode='gauge+number',
        value=round(score, 1),
        number={'suffix': '%', 'font': {'size': 36, 'color': color,
                                         'family': 'Nunito, sans-serif'}},
        domain={'x': [0.1, 0.9], 'y': [0.15, 0.95]},                                 
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1,
                     'tickcolor': C['border'], 'tickfont': {'size': 9}},
            'bar': {'color': color, 'thickness': 0.72},
            'bgcolor': C['light_bg'], 'borderwidth': 0,
            'steps': [
                {'range': [0, 50],   'color': '#FFEBEE'},
                {'range': [50, 75],  'color': '#FFF3E0'},
                {'range': [75, 100], 'color': '#E8F5E9'},
            ],
            'threshold': {'line': {'color': C['primary'], 'width': 2},
                          'thickness': 0.75, 'value': 80},
        },
        title={'text': '<b>Overall Project Health</b><br>'
                       '<span style="font-size:11px">Weighted composite — 6 datasets</span>',
               'font': {'size': 13, 'color': C['primary'],
                        'family': 'Nunito, sans-serif'}},
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        height=230,
        margin=dict(l=30, r=30, t=50, b=10),
        font=dict(family='Nunito, sans-serif'),
    )
    return fig, round(score, 1), color


# ─────────────────────────────────────────────────────────────────────────────
# LAYOUT
# ─────────────────────────────────────────────────────────────────────────────

def layout():
    gauge_fig, score, score_color = _project_score_gauge()

    # Status label
    if score >= 75:
        status_txt = '● ON TRACK'
        status_c, status_bg = C['success'], C['success_bg']
    elif score >= 55:
        status_txt = '⚠ ATTENTION REQUIRED'
        status_c, status_bg = C['warning'], C['warning_bg']
    else:
        status_txt = '⚠ CRITICAL'
        status_c, status_bg = C['danger'], C['danger_bg']

    # Critical alerts list
    alerts = _build_alerts()

    return html.Div([

        # ── PAGE HEADER ──────────────────────────────────────────────────────
        html.Div([
            html.Div([
                html.H2('Executive Summary', style={
                    'margin': '0 0 4px 0', 'fontWeight': '900',
                    'fontSize': '26px', 'color': C['primary'],
                }),
                html.P(
                    'IMCE Project Rwanda — Integrated Monitoring of Environmental & Social Commitments — '
                    '6 datasets · 152 surveys · 5 districts',
                    style={'margin': '0', 'color': C['muted'], 'fontSize': '13px'},
                ),
            ]),
            html.Span(status_txt, style={
                'background': status_bg, 'color': status_c,
                'padding': '7px 18px', 'borderRadius': '20px',
                'fontSize': '13px', 'fontWeight': '800',
                'border': f'1px solid {status_c}',
            }),
        ], style={
            'display': 'flex', 'justifyContent': 'space-between',
            'alignItems': 'center', 'marginBottom': '24px',
        }),

        # ── TOP KPIs ─────────────────────────────────────────────────────────
        dbc.Row([
            dbc.Col(kpi_card('👥', 'PAPs Compensated',
                             f'{M["paps_comp"]}/{M["paps_total"]}',
                             f'{M["paps_comp_pct"]:.0f}% — {M["paps_unsat"]} unsatisfied',
                             C['p1'],
                             alert=M['paps_comp_pct'] < 80), md=2),
            dbc.Col(kpi_card('⚒️', 'Workers Trained',
                             f'{M["w_trained"]}/{M["w_total"]}',
                             f'{M["w_trained_pct"]:.0f}% — {M["w_female"]} women ({M["w_female_pct"]:.0f}%)',
                             C['p2'],
                             alert=M['w_trained_pct'] < 60), md=2),
            dbc.Col(kpi_card('🏗️', 'Contractor Incidents',
                             f'{M["c_incident"]}/{M["c_total"]}',
                             f'{M["c_incident_pct"]:.0f}% of sites reported incidents',
                             C['p4'],
                             alert=M['c_incident_pct'] > 50), md=2),
            dbc.Col(kpi_card('📋', 'GRC Resolution Rate',
                             f'{M["g_res_rate"]:.0f}%',
                             f'{M["g_resolved"]}/{M["g_complaints"]} resolved · {M["g_pending"]} pending',
                             C['p5'],
                             alert=M['g_res_rate'] < 60), md=2),
            dbc.Col(kpi_card('🗺️', 'District Compensation',
                             f'{M["d_comp_rate"]:.0f}%',
                             f'{M["d_pending"]} HH pending across {M["d_total"]} districts',
                             C['p3'],
                             alert=M['d_comp_rate'] < 60), md=2),
            dbc.Col(kpi_card('✅', 'Site Audit Score',
                             '40/40',
                             f'100% conform · {M["chk_comp_pct"]:.0f}% compensation progress',
                             C['p6']), md=2),
        ], className='g-3', style={'marginBottom': '24px'}),

        # ── CRITICAL ALERTS ───────────────────────────────────────────────────
        dbc.Row([
            dbc.Col([card([
                sec_title('⚠️ Critical Alerts',
                          'Issues requiring immediate attention from project management'),
                html.Div(alerts),
            ])], md=8),
            dbc.Col([card([
                sec_title('Overall Project Health',
                          'Weighted composite score across all 6 monitoring dimensions'),
                dcc.Graph(figure=gauge_fig, config={'displayModeBar': False},
                          style={'height': '230px'}),
            ])], md=4),
        ], className='g-3', style={'marginBottom': '24px'}),

        # ── PROJECT HEALTH RADAR ──────────────────────────────────────────────
        dbc.Row([
            dbc.Col([card([
                sec_title('Project Health Radar',
                          'Six monitoring dimensions vs 80% World Bank target benchmark'),
                dcc.Graph(figure=_radar_fig(), config={'displayModeBar': False},
                          style={'height': '340px'}),
            ])], md=5),
            dbc.Col([card([
                sec_title('Monitoring Coverage Timeline',
                          'Survey dates across all 5 datasets — bubble size = number of surveys that day'),
                dcc.Graph(figure=_timeline_fig(), config={'displayModeBar': False},
                          style={'height': '340px'}),
            ])], md=7),
        ], className='g-3', style={'marginBottom': '24px'}),

        # ── DIMENSION SCORECARD ───────────────────────────────────────────────
        dbc.Row([dbc.Col([card([
            sec_title('Dimension Scorecard',
                      'Quick health indicator for each monitoring dimension'),
            _dimension_scorecard(),
        ])], md=12)], className='g-3', style={'marginBottom': '24px'}),

        # ── DATASET CARDS ─────────────────────────────────────────────────────
        html.H5('Dataset Deep-Dives', style={
            'fontWeight': '800', 'fontSize': '15px', 'color': C['primary'],
            'marginBottom': '14px',
        }),
        dbc.Row([
            dbc.Col([_paps_card()],        md=4, style={'marginBottom': '16px'}),
            dbc.Col([_workers_card()],     md=4, style={'marginBottom': '16px'}),
            dbc.Col([_contractors_card()], md=4, style={'marginBottom': '16px'}),
        ], className='g-3'),
        dbc.Row([
            dbc.Col([_grc_card()],       md=4, style={'marginBottom': '16px'}),
            dbc.Col([_district_card()],  md=4, style={'marginBottom': '16px'}),
            dbc.Col([_checklist_card()], md=4, style={'marginBottom': '16px'}),
        ], className='g-3'),

    ], style={
        'padding': '32px 32px 48px 252px',
        'minHeight': '100vh',
        'background': C['light_bg'],
    })


# ─────────────────────────────────────────────────────────────────────────────
# ALERT BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def _build_alerts():
    alerts = []

    # Rubavu anomaly
    for _, r in DISTRICT.iterrows():
        if r['not_yet_compensated_count'] > r['households_affected']:
            alerts.append(alert_row(
                '🔴', f"{r['district_name']} — Cross-phase compensation backlog: "
                f"{int(r['not_yet_compensated_count'])} pending vs {int(r['households_affected'])} "
                f"registered households. Immediate World Bank escalation required.",
                C['danger'], C['danger_bg'],
            ))

    # Critical district comp < 30%
    for _, r in DISTRICT[DISTRICT['compensation_progress'] < 30].iterrows():
        if r['not_yet_compensated_count'] <= r['households_affected']:
            alerts.append(alert_row(
                '🔴', f"{r['district_name']} ({r['site_name']}) — Compensation rate at "
                f"{r['compensation_progress']:.0f}%. {int(r['not_yet_compensated_count'])} households uncompensated.",
                C['danger'], C['danger_bg'],
            ))

    # Contractor incidents > 70%
    if M['c_incident_pct'] >= 70:
        alerts.append(alert_row(
            '🟠', f"{M['c_incident']}/{M['c_total']} contractor sites reported safety incidents "
            f"({M['c_incident_pct']:.0f}%). OHS compliance requires systematic review.",
            C['warning'], C['warning_bg'],
        ))

    # Worker training gap
    untrained = M['w_total'] - M['w_trained']
    if untrained > 0:
        alerts.append(alert_row(
            '🟠', f"{untrained} workers ({100 - M['w_trained_pct']:.0f}%) have received zero training — "
            f"no health/safety, GBV, or HIV awareness sessions recorded.",
            C['warning'], C['warning_bg'],
        ))

    # GBV training gap in workers
    gbv_trained = int((WORKERS['train_gbv'] == 1).sum())
    if gbv_trained < len(WORKERS) * 0.5:
        alerts.append(alert_row(
            '🟠', f"Only {gbv_trained}/{len(WORKERS)} workers ({gbv_trained/len(WORKERS)*100:.0f}%) "
            f"received GBV/SEA awareness training — below the 50% threshold.",
            C['warning'], C['warning_bg'],
        ))

    # GRC unresolved
    unresolved_paps = int((PAPS['grievance_resolved'] == 'Not resolved').sum())
    if unresolved_paps > 5:
        alerts.append(alert_row(
            '🟡', f"{unresolved_paps} PAP grievances remain unresolved out of "
            f"{int((PAPS['grievance_submitted'] == 'Yes').sum())} submitted — "
            f"GRC follow-up required.",
            C['p3'], '#FFF8E1',
        ))

    # Checklist compensation paradox
    alerts.append(alert_row(
        '🟡', f"Cyuve site (Musanze) — 100% procedurally compliant but only "
        f"{M['chk_comp_pct']:.0f}% of PAPs compensated after "
        f"{int(CHECKLIST.iloc[0]['compensation_timing_months'])} months. "
        f"Formal compliance masks substantive gap.",
        C['p3'], '#FFF8E1',
    ))

    return alerts if alerts else html.Div(
        html.Span('✓ No critical alerts', style={
            'color': C['success'], 'fontWeight': '700', 'fontSize': '14px',
        }), style={'padding': '12px'}
    )


# ─────────────────────────────────────────────────────────────────────────────
# DIMENSION SCORECARD
# ─────────────────────────────────────────────────────────────────────────────

def _dimension_scorecard():
    dims = [
        ('👥 PAP Compensation',      M['paps_comp_pct'],        'Households compensated'),
        ('⚒️ Worker Training',        M['w_trained_pct'],        'Workers with any training'),
        ('🏗️ Contractor Safety',      100 - M['c_incident_pct'], 'Sites without incidents'),
        ('📋 GRC Resolution',          M['g_res_rate'],           'Complaints resolved'),
        ('🗺️ District Compensation',  min(M['d_comp_rate'], 100),'Weighted HH compensation rate'),
        ('✅ Site Audit Compliance',   M['chk_comply'],           'Audit indicators conform'),
    ]

    cells = []
    for label, pct, desc in dims:
        color = C['success'] if pct >= 75 else (C['warning'] if pct >= 50 else C['danger'])
        bg    = C['success_bg'] if pct >= 75 else (C['warning_bg'] if pct >= 50 else C['danger_bg'])
        cells.append(dbc.Col([
            html.Div([
                html.Div(label, style={
                    'fontSize': '12px', 'fontWeight': '700',
                    'color': C['primary'], 'marginBottom': '8px',
                }),
                html.H3(f'{pct:.0f}%', style={
                    'margin': '0 0 4px', 'fontWeight': '900',
                    'fontSize': '26px', 'color': color,
                }),
                html.Div(html.Div(style={
                    'width': f'{min(pct, 100):.0f}%',
                    'height': '4px', 'background': color, 'borderRadius': '2px',
                }), style={
                    'background': C['border'], 'borderRadius': '2px',
                    'marginBottom': '6px', 'overflow': 'hidden',
                }),
                html.Div(desc, style={
                    'fontSize': '10px', 'color': C['muted'],
                }),
            ], style={
                'background': bg, 'borderRadius': '10px',
                'padding': '14px 16px', 'border': f'1px solid {color}30',
            }),
        ], md=2))

    return dbc.Row(cells, className='g-3')


# ─────────────────────────────────────────────────────────────────────────────
# DATASET CARDS
# ─────────────────────────────────────────────────────────────────────────────

def _paps_card():
    status = '✓ On Track' if M['paps_comp_pct'] >= 80 else '⚠ Review'
    sc = C['success'] if M['paps_comp_pct'] >= 80 else C['warning']
    return dataset_card(
        '👥', 'Project Affected Persons', C['p1'],
        [
            mini_prog('Compensated', M['paps_comp_pct'],
                      C['success'] if M['paps_comp_pct'] >= 80 else C['warning']),
            mini_prog('GRM Aware', M['paps_grm_aware'] / M['paps_total'] * 100, C['p1']),
            mini_prog('Valuation Explained', 48 / 52 * 100, C['p2']),
            html.Div([
                html.Span(f'{M["paps_grievance"]} grievances submitted · ', style={'fontSize': '11px', 'color': C['muted']}),
                html.Span(f'{M["paps_resolved"]} fully resolved', style={'fontSize': '11px', 'color': C['danger'], 'fontWeight': '700'}),
            ]),
        ],
        '/paps', status, sc,
    )


def _workers_card():
    status = '⚠ Training Gap' if M['w_trained_pct'] < 70 else '✓ On Track'
    sc = C['warning'] if M['w_trained_pct'] < 70 else C['success']
    return dataset_card(
        '⚒️', 'Workers', C['p2'],
        [
            mini_prog('Trained (any)', M['w_trained_pct'],
                      C['success'] if M['w_trained_pct'] >= 70 else C['warning']),
            mini_prog('Female Workers', M['w_female_pct'], C['p5']),
            mini_prog('Health & Safety Training',
                      int((WORKERS['train_health_safety'] == 1).sum()) / M['w_total'] * 100, C['p2']),
            mini_prog('GBV Awareness Training',
                      int((WORKERS['train_gbv'] == 1).sum()) / M['w_total'] * 100, C['p4']),
        ],
        '/workers', status, sc,
    )


def _contractors_card():
    status = '⚠ Incidents' if M['c_incident_pct'] > 50 else '✓ On Track'
    sc = C['danger'] if M['c_incident_pct'] > 50 else C['success']
    return dataset_card(
        '🏗️', 'Contractors', C['p3'],
        [
            mini_prog('Sites with Incidents', M['c_incident_pct'], C['danger']),
            mini_prog('Women in Workforce', M['c_avg_women'], C['p5']),
            mini_prog('Local Workforce', M['c_avg_local'], C['p2']),
            mini_prog('PPE Compliance (helmet)', 100.0, C['success']),
        ],
        '/contractors', status, sc,
    )


def _grc_card():
    status = '✓ Functional' if M['g_res_rate'] >= 60 else '⚠ Review'
    sc = C['success'] if M['g_res_rate'] >= 60 else C['warning']
    # Most common complaint type
    complaint_cols = {
        'complaint_household_conflict': 'Household conflict',
        'complaint_valuation_error': 'Valuation error',
        'complaint_late_payment': 'Late payment',
        'complaint_valuation_refusal': 'Valuation refusal',
    }
    top_complaint = max(complaint_cols, key=lambda c: int(GRC[c].sum()))
    top_label = complaint_cols[top_complaint]
    top_count = int(GRC[top_complaint].sum())

    return dataset_card(
        '📋', 'Grievance Committees (GRC)', C['p5'],
        [
            mini_prog('Resolution Rate', M['g_res_rate'],
                      C['success'] if M['g_res_rate'] >= 60 else C['warning']),
            mini_prog('Training Coverage', 100.0, C['success']),
            mini_prog('Logbook Coverage', 100.0, C['success']),
            html.Div([
                html.Span('Top complaint: ', style={'fontSize': '11px', 'color': C['muted']}),
                html.Span(f'{top_label} ({top_count} GRCs)', style={
                    'fontSize': '11px', 'color': C['danger'], 'fontWeight': '700',
                }),
            ]),
        ],
        '/grc', status, sc,
    )


def _district_card():
    status = '⚠ Critical' if M['d_comp_rate'] < 50 else ('⚠ Review' if M['d_comp_rate'] < 75 else '✓ On Track')
    sc = C['danger'] if M['d_comp_rate'] < 50 else (C['warning'] if M['d_comp_rate'] < 75 else C['success'])

    # Instruments: count districts with 100% instruments
    inst_cols = ['inst_esmf_rpf','inst_lmp','inst_sep','inst_esia','inst_esmf',
                 'inst_gbv_sea_plan','permit_eia_cert','permit_eia_conditions','permit_borrow_pit']
    full_inst = int((DISTRICT[inst_cols].sum(axis=1) == len(inst_cols)).sum())

    return dataset_card(
        '🗺️', 'District Monitoring', C['p6'],
        [
            mini_prog('Weighted Compensation Rate', min(M['d_comp_rate'], 100),
                      C['danger'] if M['d_comp_rate'] < 50 else C['warning']),
            mini_prog('Districts with Full Instruments', full_inst / 5 * 100, C['p2']),
            mini_prog('Districts with E&S Staff', 3 / 5 * 100, C['p1']),
            html.Div([
                html.Span(f'{M["d_pending"]} total households ', style={'fontSize': '11px', 'color': C['muted']}),
                html.Span('awaiting compensation', style={
                    'fontSize': '11px', 'color': C['danger'], 'fontWeight': '700',
                }),
            ]),
        ],
        '/district', status, sc,
    )


def _checklist_card():
    return dataset_card(
        '✅', 'Site Audit — Checklist', C['p6'],
        [
            mini_prog('Procedural Compliance', 100.0, C['success']),
            mini_prog('Compensation Progress', M['chk_comp_pct'], C['danger']),
            mini_prog('Staff Deployed (E&S)', 100.0, C['success']),
            html.Div([
                html.Span('8 dedicated E&S personnel · ', style={'fontSize': '11px', 'color': C['muted']}),
                html.Span('6 GRCs established', style={
                    'fontSize': '11px', 'color': C['p2'], 'fontWeight': '700',
                }),
            ]),
        ],
        '/checklist', '✓ Benchmark Site', C['success'],
    )


# ─────────────────────────────────────────────────────────────────────────────
# CALLBACKS
# ─────────────────────────────────────────────────────────────────────────────

def register_callbacks(app):
    pass  # Static summary page — no interactive filters