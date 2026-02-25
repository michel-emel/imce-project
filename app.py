"""
IMCE Dashboard v2 — PAPs + Workers + Contractors + GRC pages
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output

from pages.paps_page        import layout as paps_layout,        register_callbacks as reg_paps
from pages.workers_page     import layout as workers_layout,     register_callbacks as reg_workers
from pages.contractors_page import layout as contractors_layout, register_callbacks as reg_contractors
from pages.grc_page         import layout as grc_layout,         register_callbacks as reg_grc
from pages.district_page    import layout as district_layout,    register_callbacks as reg_district
from pages.checklist_page   import layout as checklist_layout,   register_callbacks as reg_checklist
from pages.executive_summary import layout as exec_summary_layout, register_callbacks as reg_exec_summary
from pages.cross_analysis    import layout as cross_layout,         register_callbacks as reg_cross

C = {
    'primary': '#0D2137', 'secondary': '#00BFA5',
    'light_bg': '#F0F4F8', 'card': '#FFFFFF',
    'muted': '#607D8B', 'border': '#E0E8F0',
}

NAV = [
    ('/',             '🏠', 'Executive Summary'),
    ('/paps',         '👥', 'Project Affected Persons'),
    ('/workers',      '⚒️',  'Workers'),
    ('/contractors',  '🏗️',  'Contractors'),
    ('/grc',          '📋', 'Grievance Committees'),
    ('/district',     '🗺️',  'District Monitoring'),
    ('/checklist',    '✅', 'Site Audit — Checklist'),
    ('/crossanalysis','🔗', 'Cross Analysis'),
]

def sidebar():
    return html.Div([
        html.Div([
            html.Div('IMCE', style={
                'fontSize': '22px', 'fontWeight': '900',
                'color': 'white', 'letterSpacing': '3px',
            }),
            html.Div('E&S Monitoring', style={
                'fontSize': '10px', 'color': C['secondary'],
                'letterSpacing': '2px', 'fontWeight': '600',
                'textTransform': 'uppercase',
            }),
        ], style={
            'padding': '28px 24px 24px',
            'borderBottom': '1px solid rgba(255,255,255,0.08)',
            'marginBottom': '8px',
        }),
        html.Nav(id='sidebar-nav'),
        html.Div([
            html.Div('World Bank Project', style={
                'fontSize': '10px', 'color': 'rgba(255,255,255,0.3)',
                'textTransform': 'uppercase', 'letterSpacing': '1px',
            }),
            html.Div('Rwanda', style={
                'fontSize': '10px', 'color': 'rgba(255,255,255,0.3)',
            }),
        ], style={'padding': '20px 24px', 'marginTop': 'auto'}),
    ], style={
        'width': '220px', 'minWidth': '220px', 'background': C['primary'],
        'height': '100vh', 'position': 'fixed', 'left': '0', 'top': '0',
        'display': 'flex', 'flexDirection': 'column', 'zIndex': '100',
    })


def placeholder(title, icon, msg):
    return html.Div([
        html.H2(f'{icon} {title}', style={
            'margin': '0 0 24px', 'fontWeight': '900',
            'fontSize': '24px', 'color': C['primary'],
        }),
        html.Div([
            html.Div(icon, style={'fontSize': '48px', 'marginBottom': '16px'}),
            html.H4('Coming Soon', style={'color': C['primary'], 'marginBottom': '8px'}),
            html.P(msg, style={'color': C['muted'], 'maxWidth': '400px',
                               'textAlign': 'center'}),
        ], style={
            'background': C['card'], 'borderRadius': '12px',
            'padding': '60px 40px', 'textAlign': 'center',
            'boxShadow': '0 2px 8px rgba(13,33,55,0.08)',
        }),
    ], style={
        'padding': '32px 32px 32px 252px',
        'minHeight': '100vh', 'background': C['light_bg'],
    })


app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        'https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap',
    ],
    suppress_callback_exceptions=True,
    title='IMCE — E&S Monitoring',
)

server = app.server

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    sidebar(),
    html.Div(id='page-content'),
], style={'fontFamily': 'Nunito, sans-serif'})


@app.callback(Output('sidebar-nav', 'children'), Input('url', 'pathname'))
def update_sidebar(pathname):
    current = pathname or '/'
    links = []
    for path, icon, label in NAV:
        is_active = (current == path) or (path == '/' and current not in [p for p, _, _ in NAV if p != '/'])
        if is_active:
            style = {
                'display': 'flex', 'alignItems': 'center', 'gap': '12px',
                'padding': '11px 17px 11px 17px', 'margin': '2px 12px',
                'borderRadius': '8px',
                'color': 'white', 'textDecoration': 'none',
                'background': 'rgba(255,255,255,0.12)',
                'borderLeft': '3px solid ' + C['secondary'],
            }
            label_style = {'fontSize': '13px', 'fontWeight': '800', 'color': 'white'}
        else:
            style = {
                'display': 'flex', 'alignItems': 'center', 'gap': '12px',
                'padding': '11px 20px', 'margin': '2px 12px',
                'borderRadius': '8px',
                'color': 'rgba(255,255,255,0.55)', 'textDecoration': 'none',
            }
            label_style = {'fontSize': '13px', 'fontWeight': '600'}
        links.append(dcc.Link([
            html.Span(icon,  style={'fontSize': '16px', 'width': '24px', 'display': 'inline-block'}),
            html.Span(label, style=label_style),
        ], href=path, style=style, className='nav-link-item'))
    return links


@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def render(pathname):
    if pathname == '/paps':
        return paps_layout()
    elif pathname == '/workers':
        return workers_layout()
    elif pathname == '/contractors':
        return contractors_layout()
    elif pathname == '/grc':
        return grc_layout()
    elif pathname == '/district':
        return district_layout()
    elif pathname == '/checklist':
        return checklist_layout()
    elif pathname == '/crossanalysis':
        return cross_layout()
    else:
        return exec_summary_layout()


reg_paps(app)
reg_workers(app)
reg_contractors(app)
reg_grc(app)
reg_district(app)
reg_checklist(app)
reg_exec_summary(app)
reg_cross(app)

app.index_string = '''<!DOCTYPE html>
<html>
<head>{%metas%}<title>{%title%}</title>{%favicon%}{%css%}
<style>
  * { box-sizing: border-box; }
  body { margin: 0; background: #F0F4F8; }
  .nav-link-item:hover {
    background: rgba(255,255,255,0.1) !important;
    color: white !important;
  }
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: #F0F4F8; }
  ::-webkit-scrollbar-thumb { background: #B0BEC5; border-radius: 3px; }
</style>
</head>
<body>{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer></body>
</html>'''

if __name__ == '__main__':
    app.run(debug=True)
    # app.run(debug=True, port=8050)