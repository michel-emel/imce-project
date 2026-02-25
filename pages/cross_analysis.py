"""
IMCE Dashboard — Cross Analysis
Surfaces insights that are invisible within any single dataset.
5 analytical angles crossing PAPs × Workers × Contractors × GRC × District.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from dash import dcc, html, Input, Output
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

PALETTE = [C['p1'], C['p2'], C['p3'], C['p4'], C['p5'], C['p6']]

BASE_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Nunito, sans-serif', color=C['primary'], size=13),
    margin=dict(l=10, r=10, t=40, b=10),
    hoverlabel=dict(bgcolor=C['primary'], bordercolor=C['border'],
                    font=dict(family='Nunito, sans-serif', size=13)),
    xaxis=dict(gridcolor=C['border'], linecolor=C['border'], tickfont=dict(size=12)),
    yaxis=dict(gridcolor=C['border'], linecolor=C['border'], tickfont=dict(size=12)),
    legend=dict(bgcolor='rgba(255,255,255,0.9)', bordercolor=C['border'],
                borderwidth=1, font=dict(size=12)),
)

# ─────────────────────────────────────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────────────────────────────────────

def _path(f):
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), f)


PAPS        = pd.read_csv(_path('PAPs_clean.csv'))
WORKERS     = pd.read_csv(_path('workers_clean.csv'))
CONTRACTORS = pd.read_csv(_path('contractors_clean.csv'))
GRC         = pd.read_csv(_path('GRC_clean.csv'))
DISTRICT    = pd.read_csv(_path('district_clean.csv'))
CHECKLIST   = pd.read_csv(_path('checklist_clean.csv'))

# Normalize district names for joining
def norm_district(s):
    if pd.isna(s):
        return ''
    return str(s).strip().lower().replace(' district', '').replace('district', '').strip()

DISTRICT['district_key'] = DISTRICT['district_name'].apply(norm_district)
GRC['district_key']      = GRC['district'].apply(norm_district)
PAPS['district_key']     = PAPS['district'].apply(norm_district)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def card(children, style=None):
    base = {
        'background': C['card'], 'borderRadius': '12px',
        'padding': '22px 26px',
        'boxShadow': '0 2px 8px rgba(13,33,55,0.07)', 'height': '100%',
    }
    if style:
        base.update(style)
    return html.Div(children, style=base)


def sec_title(title, subtitle=None, tag=None):
    return html.Div([
        html.Div([
            html.H5(title, style={
                'margin': '0 0 2px 0', 'fontWeight': '700',
                'fontSize': '15px', 'color': C['primary'], 'display': 'inline',
            }),
            html.Span(f'  {tag}', style={
                'fontSize': '11px', 'fontWeight': '800',
                'background': '#E3F2FD', 'color': C['accent'],
                'padding': '2px 8px', 'borderRadius': '8px',
                'marginLeft': '8px', 'verticalAlign': 'middle',
            }) if tag else html.Span(),
        ]),
        html.P(subtitle, style={'margin': '0', 'fontSize': '12px', 'color': C['muted']})
        if subtitle else html.Span(),
    ], style={'marginBottom': '16px', 'paddingBottom': '10px',
              'borderBottom': f'2px solid {C["border"]}'})


def insight_box(icon, title, text, color):
    return html.Div([
        html.Span(icon + ' ', style={'fontSize': '16px'}),
        html.Span(title, style={
            'fontWeight': '800', 'fontSize': '13px', 'color': color,
        }),
        html.P(text, style={
            'margin': '4px 0 0 0', 'fontSize': '12px',
            'color': C['muted'], 'lineHeight': '1.55',
        }),
    ], style={
        'background': color + '12', 'border': f'1px solid {color}40',
        'borderRadius': '8px', 'padding': '12px 14px', 'marginBottom': '10px',
    })


# ─────────────────────────────────────────────────────────────────────────────
# CROSS ANALYSIS 1 — GRM Awareness × Compensation Outcome (PAPs)
# ─────────────────────────────────────────────────────────────────────────────

def _cross1_fig():
    """Do GRM-aware PAPs get compensated more? — Stacked bar by GRM awareness."""
    df = PAPS.copy()
    df['grm_label'] = df['grm_aware'].map({'Yes': 'GRM Aware', 'No': 'Not GRM Aware'})
    df['comp_label'] = df['compensation_received'].map(
        {'Yes': 'Compensated', 'No': 'Not Compensated'})

    ct = df.groupby(['grm_label', 'comp_label']).size().unstack(fill_value=0)

    fig = go.Figure()
    colors = {'Compensated': C['success'], 'Not Compensated': C['danger']}
    for col in ['Compensated', 'Not Compensated']:
        if col in ct.columns:
            totals = ct.sum(axis=1)
            pcts = (ct[col] / totals * 100).round(1)
            fig.add_trace(go.Bar(
                name=col,
                x=ct.index,
                y=pcts,
                marker_color=colors[col], marker_line_width=0,
                text=[f'{p:.0f}%' for p in pcts],
                textposition='inside',
                textfont=dict(color='white', size=12),
                customdata=ct[col].values,
                hovertemplate='<b>%{x}</b><br>' + col + ': %{y:.0f}% (%{customdata})<extra></extra>',
            ))

    fig.update_layout(**BASE_LAYOUT, barmode='stack',
                      title=dict(text='', font=dict(size=13)))
    fig.update_yaxes(title='% of Group', ticksuffix='%', range=[0, 115])
    return fig


def _cross1_insights():
    df = PAPS.copy()
    aware_comp = len(df[(df['grm_aware'] == 'Yes') & (df['compensation_received'] == 'Yes')])
    aware_total = len(df[df['grm_aware'] == 'Yes'])
    unaware_comp = len(df[(df['grm_aware'] == 'No') & (df['compensation_received'] == 'Yes')])
    unaware_total = len(df[df['grm_aware'] == 'No'])
    aware_rate   = aware_comp / aware_total * 100 if aware_total else 0
    unaware_rate = unaware_comp / unaware_total * 100 if unaware_total else 0

    return [
        insight_box('🟢', f'GRM-Aware PAPs: {aware_rate:.0f}% compensated',
                    f'{aware_comp}/{aware_total} PAPs who knew the GRM received compensation.',
                    C['success']),
        insight_box('🔴', f'Non-Aware PAPs: {unaware_rate:.0f}% compensated',
                    f'{unaware_comp}/{unaware_total} PAPs unaware of GRM received compensation. '
                    f'Gap of {aware_rate - unaware_rate:.0f} percentage points.',
                    C['danger']),
        insight_box('💡', 'Policy implication',
                    'GRM awareness is a strong predictor of compensation receipt. '
                    'Investing in GRM outreach directly improves compensation outcomes.',
                    C['accent']),
    ]


# ─────────────────────────────────────────────────────────────────────────────
# CROSS ANALYSIS 2 — Worker Training × Gender
# ─────────────────────────────────────────────────────────────────────────────

def _cross2_fig():
    """Are women less trained than men across health/safety, GBV, HIV?"""
    df = WORKERS.copy()
    training_cols  = ['train_health_safety', 'train_gbv', 'train_hiv']
    training_names = ['Health & Safety', 'GBV/SEA Awareness', 'HIV Awareness']

    fig = go.Figure()
    genders = [('Male', C['p1']), ('Female', C['p4'])]
    for gender, color in genders:
        sub = df[df['gender'] == gender]
        n   = len(sub)
        rates = [sub[col].mean() * 100 for col in training_cols]
        fig.add_trace(go.Bar(
            name=gender, x=training_names, y=rates,
            marker_color=color, marker_line_width=0,
            text=[f'{r:.0f}%' for r in rates],
            textposition='outside',
            textfont=dict(size=11),
            hovertemplate=f'<b>{gender}</b><br>%{{x}}: %{{y:.0f}}%<extra></extra>',
        ))

    fig.update_layout(**BASE_LAYOUT, barmode='group')
    fig.update_yaxes(title='% Trained', ticksuffix='%', range=[0, 115])
    return fig


def _cross2_insights():
    df = WORKERS.copy()
    m = df[df['gender'] == 'Male']
    f = df[df['gender'] == 'Female']

    insights = []
    cols = [('train_health_safety', 'Health & Safety'),
            ('train_gbv', 'GBV/SEA'),
            ('train_hiv', 'HIV Awareness')]
    for col, name in cols:
        mr = m[col].mean() * 100
        fr = f[col].mean() * 100
        gap = mr - fr
        color = C['danger'] if abs(gap) > 15 else (C['warning'] if abs(gap) > 5 else C['success'])
        insights.append(insight_box(
            '⚖️', f'{name} — Gap: {abs(gap):.0f}pp',
            f'Male: {mr:.0f}% vs Female: {fr:.0f}%. '
            f'{"Women are significantly under-trained." if gap > 15 else "Training gap is acceptable." if abs(gap) <= 5 else "Moderate disparity — watch closely."}',
            color,
        ))
    return insights


# ─────────────────────────────────────────────────────────────────────────────
# CROSS ANALYSIS 3 — Contractor Incidents × PPE Gaps
# ─────────────────────────────────────────────────────────────────────────────

def _cross3_fig():
    """Do contractors with PPE gaps have more incidents?"""
    df = CONTRACTORS.copy()
    ppe_cols = ['ppe_helmet', 'ppe_earplug', 'ppe_mask', 'ppe_safety_shoes', 'ppe_gloves']
    df['ppe_score'] = df[ppe_cols].sum(axis=1)
    df['ppe_pct']   = df['ppe_score'] / len(ppe_cols) * 100
    df['incident']  = df['incidents_occurred'].map({'Yes': 1, 'No': 0})
    df['has_incident_label'] = df['incidents_occurred']

    fig = go.Figure()
    for label, color, symbol in [('Yes', C['danger'], 'x'), ('No', C['success'], 'circle')]:
        sub = df[df['incidents_occurred'] == label]
        fig.add_trace(go.Scatter(
            x=sub['ppe_pct'],
            y=sub['women_percent'],
            mode='markers',
            name=f'Incident: {label}',
            marker=dict(
                color=color, size=12,
                symbol=symbol,
                line=dict(color='white', width=1.5),
            ),
            customdata=sub[['site_name', 'total_workers', 'incidents_count']].values,
            hovertemplate=(
                '<b>%{customdata[0]}</b><br>'
                'PPE Score: %{x:.0f}%<br>'
                'Women: %{y:.0f}%<br>'
                'Workers: %{customdata[1]}<br>'
                'Incidents: %{customdata[2]}<extra></extra>'
            ),
        ))

    fig.update_layout(**BASE_LAYOUT)
    fig.update_xaxes(title='PPE Coverage Score (%)', ticksuffix='%')
    fig.update_yaxes(title='Women in Workforce (%)', ticksuffix='%')
    fig.add_annotation(
        text='✕ = Incident reported   ● = No incident',
        xref='paper', yref='paper', x=0.5, y=1.08,
        font=dict(size=11, color=C['muted']), showarrow=False,
    )
    return fig


def _cross3_insights():
    df = CONTRACTORS.copy()
    ppe_cols = ['ppe_helmet', 'ppe_earplug', 'ppe_mask', 'ppe_safety_shoes', 'ppe_gloves']
    df['ppe_score'] = df[ppe_cols].sum(axis=1) / len(ppe_cols) * 100

    incident_ppe = df[df['incidents_occurred'] == 'Yes']['ppe_score'].mean()
    no_incident_ppe = df[df['incidents_occurred'] == 'No']['ppe_score'].mean()
    incident_count_avg = df[df['incidents_occurred'] == 'Yes']['incidents_count'].mean()

    # Earplug — the most missing PPE
    earplug_gap = int((CONTRACTORS['ppe_earplug'] == 0).sum())

    return [
        insight_box('🔴', f'{int((CONTRACTORS["incidents_occurred"] == "Yes").sum())}/17 sites with incidents',
                    f'Average {incident_count_avg:.1f} incidents per affected site. '
                    f'Average PPE score on incident sites: {incident_ppe:.0f}%.',
                    C['danger']),
        insight_box('🟠', f'Earplug — most common PPE gap: {earplug_gap}/17 sites missing',
                    'Earplugs are the only PPE not universally provided. '
                    'Noise-related injuries are the likely consequence.',
                    C['warning']),
        insight_box('🟢', f'No-incident sites: avg PPE {no_incident_ppe:.0f}%',
                    'Sites without incidents have higher PPE coverage on average. '
                    'Correlation supports mandatory PPE enforcement.',
                    C['success']),
    ]


# ─────────────────────────────────────────────────────────────────────────────
# CROSS ANALYSIS 4 — GRC Resolution Rate × District Compensation Rate
# ─────────────────────────────────────────────────────────────────────────────

def _cross4_fig():
    """Districts where GRCs resolve complaints faster → better compensation rates?"""
    # GRC resolution by district
    grc_by_dist = GRC.groupby('district_key').agg(
        total_received=('complaints_received', 'sum'),
        total_resolved=('complaints_resolved', 'sum'),
        total_pending=('complaints_pending', 'sum'),
        grc_count=('district_key', 'count'),
    ).reset_index()
    grc_by_dist['resolution_rate'] = (
        grc_by_dist['total_resolved'] /
        grc_by_dist['total_received'].replace(0, np.nan) * 100
    ).fillna(0)

    # District compensation
    dist = DISTRICT[['district_key', 'district_name', 'compensation_progress',
                      'households_affected', 'not_yet_compensated_count']].copy()

    merged = pd.merge(grc_by_dist, dist, on='district_key', how='inner')

    fig = go.Figure()
    for i, row in merged.iterrows():
        comp = float(row['compensation_progress']) if pd.notna(row['compensation_progress']) else 0
        fig.add_trace(go.Scatter(
            x=[row['resolution_rate']],
            y=[comp],
            mode='markers+text',
            name=row['district_name'],
            marker=dict(
                color=PALETTE[i % len(PALETTE)],
                size=max(row['grc_count'] * 6, 10),
                line=dict(color='white', width=1.5),
            ),
            text=[row['district_name']],
            textposition='top center',
            textfont=dict(size=10),
            hovertemplate=(
                f'<b>{row["district_name"]}</b><br>'
                f'GRC Resolution Rate: {row["resolution_rate"]:.0f}%<br>'
                f'Compensation Progress: {comp:.0f}%<br>'
                f'GRC Count: {int(row["grc_count"])}<br>'
                f'Pending HH: {int(row["not_yet_compensated_count"])}<extra></extra>'
            ),
        ))

    # Quadrant lines
    fig.add_hline(y=80, line_dash='dot', line_color=C['muted'],
                  annotation_text='80% comp target', annotation_font_size=10)
    fig.add_vline(x=60, line_dash='dot', line_color=C['muted'],
                  annotation_text='60% resolution threshold', annotation_font_size=10)

    fig.update_layout(**BASE_LAYOUT, showlegend=False)
    fig.update_xaxes(title='GRC Complaint Resolution Rate (%)', ticksuffix='%')
    fig.update_yaxes(title='District Compensation Progress (%)', ticksuffix='%')
    fig.add_annotation(
        text='Bubble size = number of GRCs in district',
        xref='paper', yref='paper', x=0.5, y=1.08,
        font=dict(size=11, color=C['muted']), showarrow=False,
    )
    return fig


def _cross4_insights():
    grc_by_dist = GRC.groupby('district_key').agg(
        total_received=('complaints_received', 'sum'),
        total_resolved=('complaints_resolved', 'sum'),
    ).reset_index()
    grc_by_dist['resolution_rate'] = (
        grc_by_dist['total_resolved'] /
        grc_by_dist['total_received'].replace(0, np.nan) * 100
    ).fillna(0)
    dist = DISTRICT[['district_key', 'district_name', 'compensation_progress']].copy()
    merged = pd.merge(grc_by_dist, dist, on='district_key', how='inner')

    corr = merged['resolution_rate'].corr(merged['compensation_progress'].fillna(0))

    return [
        insight_box('📊', f'Correlation: {corr:.2f}',
                    'Positive correlation between GRC resolution rate and compensation progress. '
                    'Districts with active, resolving GRCs tend to progress faster on compensation.',
                    C['accent']),
        insight_box('🔴', 'Districts with most GRCs don\'t have highest compensation',
                    'Rubavu has the most GRCs (6) but only 13% compensation — suggesting '
                    'GRC quantity alone is insufficient. Quality of resolution matters.',
                    C['danger']),
        insight_box('💡', 'Recommendation',
                    'Focus on GRC resolution quality, not just establishment. '
                    'Track time-to-resolution per district and tie it to compensation KPIs.',
                    C['p2']),
    ]


# ─────────────────────────────────────────────────────────────────────────────
# CROSS ANALYSIS 5 — PAP Complaint vs Impact Type
# ─────────────────────────────────────────────────────────────────────────────

def _cross5_fig():
    """Which impact types drive the most grievances?"""
    df = PAPS.copy()
    # Simplify impact type
    def simplify_impact(t):
        t = str(t)
        if 'Loss of house' in t:
            return 'House Loss'
        elif 'Loss of land' in t and 'Trees' in t:
            return 'Land + Crops'
        elif 'Loss of land' in t:
            return 'Land Loss'
        elif 'Trees' in t:
            return 'Trees/Crops'
        elif 'Other' in t:
            return 'Other'
        return 'Mixed/Other'

    df['impact_simple'] = df['impact_type'].apply(simplify_impact)
    df['filed_grievance'] = (df['grievance_submitted'] == 'Yes').astype(int)
    df['not_compensated'] = (df['compensation_received'] == 'No').astype(int)
    df['unsatisfied']     = (df['compensation_satisfied'] == 'No').astype(int)

    grouped = df.groupby('impact_simple').agg(
        count=('impact_simple', 'count'),
        grievance_rate=('filed_grievance', 'mean'),
        uncompensated_rate=('not_compensated', 'mean'),
        unsatisfied_rate=('unsatisfied', 'mean'),
    ).reset_index()
    grouped = grouped.sort_values('grievance_rate', ascending=True)

    fig = go.Figure()
    for col, name, color in [
        ('grievance_rate',    'Grievance Rate',         C['p4']),
        ('uncompensated_rate','Not Compensated Rate',   C['p3']),
        ('unsatisfied_rate',  'Dissatisfied Rate',      C['p5']),
    ]:
        fig.add_trace(go.Bar(
            name=name,
            y=grouped['impact_simple'],
            x=grouped[col] * 100,
            orientation='h',
            marker_color=color, marker_line_width=0,
            text=[(f'{v*100:.0f}% ({int(c)})') for v, c in
                  zip(grouped[col], grouped['count'])],
            textposition='outside',
            textfont=dict(size=10),
        ))

    fig.update_layout(**BASE_LAYOUT, barmode='group')
    fig.update_xaxes(title='Rate (%)', ticksuffix='%', range=[0, 115])
    fig.update_yaxes(tickfont=dict(size=11))
    return fig


def _cross5_insights():
    df = PAPS.copy()
    def simplify_impact(t):
        t = str(t)
        if 'Loss of house' in t:
            return 'House Loss'
        elif 'Loss of land' in t and 'Trees' in t:
            return 'Land + Crops'
        elif 'Loss of land' in t:
            return 'Land Loss'
        elif 'Trees' in t:
            return 'Trees/Crops'
        elif 'Other' in t:
            return 'Other'
        return 'Mixed/Other'

    df['impact_simple'] = df['impact_type'].apply(simplify_impact)
    df['filed_grievance'] = (df['grievance_submitted'] == 'Yes').astype(int)
    df['not_compensated'] = (df['compensation_received'] == 'No').astype(int)

    by_impact = df.groupby('impact_simple').agg(
        n=('impact_simple', 'count'),
        griev=('filed_grievance', 'mean'),
        uncomp=('not_compensated', 'mean'),
    )
    highest_griev = by_impact['griev'].idxmax()
    highest_uncomp = by_impact['uncomp'].idxmax()

    return [
        insight_box('🔴', f'"{highest_griev}" — highest grievance rate',
                    f'{by_impact.loc[highest_griev, "griev"]*100:.0f}% of PAPs with '
                    f'{highest_griev.lower()} filed a grievance. '
                    'This impact type requires priority attention.',
                    C['danger']),
        insight_box('🟠', f'"{highest_uncomp}" — highest uncompensated rate',
                    f'{by_impact.loc[highest_uncomp, "uncomp"]*100:.0f}% of PAPs with '
                    f'{highest_uncomp.lower()} have not received compensation. '
                    'Complex valuations may be causing delays.',
                    C['warning']),
        insight_box('💡', 'Grievance ≠ Uncompensated',
                    'Some impact types generate high grievances but have good compensation rates. '
                    'Grievances reflect dissatisfaction with process, not just outcome gaps.',
                    C['accent']),
    ]


# ─────────────────────────────────────────────────────────────────────────────
# LAYOUT
# ─────────────────────────────────────────────────────────────────────────────

def layout():
    return html.Div([

        # PAGE HEADER
        html.Div([
            html.Div([
                html.H2('Cross Analysis', style={
                    'margin': '0 0 4px 0', 'fontWeight': '900',
                    'fontSize': '26px', 'color': C['primary'],
                }),
                html.P(
                    'Insights that emerge only when crossing datasets — '
                    'PAPs × Workers × Contractors × GRC × District',
                    style={'margin': '0', 'color': C['muted'], 'fontSize': '13px'},
                ),
            ]),
            html.Span('5 Cross-Dataset Analyses', style={
                'background': '#E3F2FD', 'color': C['accent'],
                'padding': '6px 16px', 'borderRadius': '20px',
                'fontSize': '13px', 'fontWeight': '700',
                'border': f'1px solid {C["accent"]}',
            }),
        ], style={
            'display': 'flex', 'justifyContent': 'space-between',
            'alignItems': 'center', 'marginBottom': '28px',
        }),

        # ── ANALYSIS 1 ────────────────────────────────────────────────────────
        dbc.Row([
            dbc.Col([card([
                sec_title(
                    'GRM Awareness → Compensation Outcome',
                    'PAPs who know about the grievance mechanism — are they better compensated?',
                    tag='PAPs × GRC',
                ),
                dcc.Graph(figure=_cross1_fig(),
                          config={'displayModeBar': False}, style={'height': '260px'}),
            ])], md=7),
            dbc.Col([card([
                sec_title('Key Findings', tag='Analysis 1'),
                html.Div(_cross1_insights()),
            ])], md=5),
        ], className='g-3', style={'marginBottom': '24px'}),

        # ── ANALYSIS 2 ────────────────────────────────────────────────────────
        dbc.Row([
            dbc.Col([card([
                sec_title('Key Findings', tag='Analysis 2'),
                html.Div(_cross2_insights()),
            ])], md=5),
            dbc.Col([card([
                sec_title(
                    'Training Gap by Gender',
                    'Are women workers receiving equivalent E&S training to men?',
                    tag='Workers × Gender',
                ),
                dcc.Graph(figure=_cross2_fig(),
                          config={'displayModeBar': False}, style={'height': '260px'}),
            ])], md=7),
        ], className='g-3', style={'marginBottom': '24px'}),

        # ── ANALYSIS 3 ────────────────────────────────────────────────────────
        dbc.Row([
            dbc.Col([card([
                sec_title(
                    'PPE Coverage vs Safety Incidents',
                    'Does PPE availability reduce incidents? Each point is a contractor site.',
                    tag='Contractors × Safety',
                ),
                dcc.Graph(figure=_cross3_fig(),
                          config={'displayModeBar': False}, style={'height': '300px'}),
            ])], md=7),
            dbc.Col([card([
                sec_title('Key Findings', tag='Analysis 3'),
                html.Div(_cross3_insights()),
            ])], md=5),
        ], className='g-3', style={'marginBottom': '24px'}),

        # ── ANALYSIS 4 ────────────────────────────────────────────────────────
        dbc.Row([
            dbc.Col([card([
                sec_title('Key Findings', tag='Analysis 4'),
                html.Div(_cross4_insights()),
            ])], md=5),
            dbc.Col([card([
                sec_title(
                    'GRC Resolution Rate × District Compensation Progress',
                    'Districts with stronger GRC activity — do they compensate PAPs faster?',
                    tag='GRC × District',
                ),
                dcc.Graph(figure=_cross4_fig(),
                          config={'displayModeBar': False}, style={'height': '300px'}),
            ])], md=7),
        ], className='g-3', style={'marginBottom': '24px'}),

        # ── ANALYSIS 5 ────────────────────────────────────────────────────────
        dbc.Row([
            dbc.Col([card([
                sec_title(
                    'Impact Type → Grievance & Compensation Rate',
                    'Which impact types drive the most grievances and uncompensated cases?',
                    tag='PAPs × Impact Type',
                ),
                dcc.Graph(figure=_cross5_fig(),
                          config={'displayModeBar': False}, style={'height': '320px'}),
            ])], md=7),
            dbc.Col([card([
                sec_title('Key Findings', tag='Analysis 5'),
                html.Div(_cross5_insights()),
            ])], md=5),
        ], className='g-3', style={'marginBottom': '24px'}),

        # ── SYNTHESIS ─────────────────────────────────────────────────────────
        dbc.Row([dbc.Col([card([
            sec_title('Cross-Dataset Synthesis',
                      'The 5 most important findings that emerge only from multi-dataset analysis'),
            dbc.Row([
                dbc.Col([insight_box(
                    '🔑', 'GRM awareness drives compensation',
                    'PAPs who know about GRM mechanisms receive compensation at significantly higher '
                    'rates. GRM outreach investment has measurable return.',
                    C['p1'],
                )], md=4),
                dbc.Col([insight_box(
                    '⚠️', 'Women workers are undertrained on GBV',
                    'Despite being closer to GBV risks, female workers receive GBV training at '
                    'lower rates than male colleagues — a systemic contradiction.',
                    C['p4'],
                )], md=4),
                dbc.Col([insight_box(
                    '🔴', 'Procedural compliance ≠ substantive progress',
                    'The Cyuve site (Checklist) demonstrates 100% procedural compliance with only '
                    '11% compensation — the gap between paper and practice is the core risk.',
                    C['danger'],
                )], md=4),
            ], className='g-3'),
            dbc.Row([
                dbc.Col([insight_box(
                    '🏗️', 'Incident rate (71%) is systemic, not exceptional',
                    '12/17 contractor sites reported incidents. With full PPE coverage except '
                    'earplugs, this suggests process gaps beyond equipment alone.',
                    C['warning'],
                )], md=4),
                dbc.Col([insight_box(
                    '📋', 'GRC quantity ≠ GRC quality',
                    'Rubavu has 6 GRCs but 145 pending households. '
                    'The number of committees does not predict resolution effectiveness.',
                    C['p5'],
                )], md=4),
                dbc.Col([insight_box(
                    '🌍', 'House loss generates highest grievance rates',
                    'PAPs experiencing house loss are most likely to file grievances and '
                    'remain uncompensated — requiring priority attention and dedicated support.',
                    C['p3'],
                )], md=4),
            ], className='g-3'),
        ])], md=12)], className='g-3'),

    ], style={
        'padding': '32px 32px 48px 252px',
        'minHeight': '100vh',
        'background': C['light_bg'],
    })


# ─────────────────────────────────────────────────────────────────────────────
# CALLBACKS
# ─────────────────────────────────────────────────────────────────────────────

def register_callbacks(app):
    pass  # All charts are static — computed from fixed datasets