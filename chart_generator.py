import os
import uuid
import numpy as np
import matplotlib
matplotlib.use('Agg')           # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

CHART_DIR = os.path.join(os.path.dirname(__file__), 'static', 'charts')
os.makedirs(CHART_DIR, exist_ok=True)

COLORS = {
    'primary':   '#4F46E5',
    'success':   '#10B981',
    'warning':   '#F59E0B',
    'danger':    '#EF4444',
    'info':      '#3B82F6',
    'purple':    '#8B5CF6',
    'bg':        '#F8FAFC',
    'text':      '#1E293B',
}


def _score_color(score):
    if score >= 80: return COLORS['success']
    if score >= 60: return COLORS['info']
    if score >= 40: return COLORS['warning']
    return COLORS['danger']


def _save(fig, prefix='chart'):
    name = f"{prefix}_{uuid.uuid4().hex[:8]}.png"
    path = os.path.join(CHART_DIR, name)
    fig.savefig(path, bbox_inches='tight', dpi=130, facecolor=COLORS['bg'])
    plt.close(fig)
    return f'charts/{name}'


# ── 1. Score overview gauge ──────────────────────────────────────────────────
def gauge_chart(ats_score):
    fig, ax = plt.subplots(figsize=(5, 3), facecolor=COLORS['bg'])
    ax.set_facecolor(COLORS['bg'])

    theta = np.linspace(np.pi, 0, 300)
    ax.plot(np.cos(theta), np.sin(theta), color='#E2E8F0', lw=18, solid_capstyle='round')

    fill_theta = np.linspace(np.pi, np.pi - np.pi * ats_score / 100, 300)
    ax.plot(np.cos(fill_theta), np.sin(fill_theta),
            color=_score_color(ats_score), lw=18, solid_capstyle='round')

    ax.text(0, 0.15, f'{ats_score}', ha='center', va='center',
            fontsize=36, fontweight='bold', color=COLORS['text'])
    ax.text(0, -0.15, 'ATS Score', ha='center', va='center',
            fontsize=11, color='#64748B')

    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-0.4, 1.2)
    ax.axis('off')
    fig.tight_layout()
    return _save(fig, 'gauge')


# ── 2. Sub-scores radar / bar ────────────────────────────────────────────────
def subscores_bar(keyword_score, skills_score, sections_score, format_score):
    labels = ['Keywords', 'Skills', 'Sections', 'Format']
    scores = [keyword_score, skills_score, sections_score, format_score]
    colors = [_score_color(s) for s in scores]

    fig, ax = plt.subplots(figsize=(6, 3.5), facecolor=COLORS['bg'])
    ax.set_facecolor(COLORS['bg'])

    bars = ax.barh(labels, scores, color=colors, height=0.5, edgecolor='white')
    ax.set_xlim(0, 110)
    ax.set_xlabel('Score', color='#64748B', fontsize=9)
    ax.tick_params(colors=COLORS['text'])
    ax.spines[['top', 'right', 'bottom']].set_visible(False)
    ax.spines['left'].set_color('#E2E8F0')
    ax.set_title('Score Breakdown', color=COLORS['text'], fontsize=12, pad=10)

    for bar, score in zip(bars, scores):
        ax.text(score + 1.5, bar.get_y() + bar.get_height() / 2,
                f'{score:.0f}%', va='center', fontsize=9, color=COLORS['text'])

    fig.tight_layout()
    return _save(fig, 'subscores')


# ── 3. Keyword match donut ───────────────────────────────────────────────────
def keyword_donut(matched, missing):
    n_matched = len(matched)
    n_missing = len(missing)
    total     = n_matched + n_missing or 1

    fig, ax = plt.subplots(figsize=(4.5, 4), facecolor=COLORS['bg'])
    ax.set_facecolor(COLORS['bg'])

    sizes  = [n_matched, n_missing]
    colors = [COLORS['success'], COLORS['danger']]
    wedges, _ = ax.pie(
        sizes, colors=colors, startangle=90,
        wedgeprops=dict(width=0.55, edgecolor='white', linewidth=2)
    )
    ax.text(0, 0, f'{n_matched}/{total}', ha='center', va='center',
            fontsize=16, fontweight='bold', color=COLORS['text'])
    ax.text(0, -0.22, 'Matched', ha='center', va='center',
            fontsize=9, color='#64748B')

    legend = [
        mpatches.Patch(color=COLORS['success'], label=f'Matched ({n_matched})'),
        mpatches.Patch(color=COLORS['danger'],  label=f'Missing ({n_missing})'),
    ]
    ax.legend(handles=legend, loc='lower center', frameon=False,
              fontsize=9, ncol=2, bbox_to_anchor=(0.5, -0.08))
    ax.set_title('Keyword Match', color=COLORS['text'], fontsize=12, pad=8)
    fig.tight_layout()
    return _save(fig, 'keywords')


# ── 4. Skills bar chart ──────────────────────────────────────────────────────
def skills_chart(extracted_skills):
    if not extracted_skills:
        return None

    skills = extracted_skills[:12]
    x      = list(range(len(skills)))

    fig, ax = plt.subplots(figsize=(7, 3.5), facecolor=COLORS['bg'])
    ax.set_facecolor(COLORS['bg'])

    bars = ax.bar(x, [1] * len(skills), color=COLORS['primary'],
                  alpha=0.85, edgecolor='white')
    ax.set_xticks(x)
    ax.set_xticklabels([s.upper() for s in skills],
                       rotation=35, ha='right', fontsize=8, color=COLORS['text'])
    ax.set_yticks([])
    ax.spines[['top', 'right', 'left', 'bottom']].set_visible(False)
    ax.set_title('Detected Skills', color=COLORS['text'], fontsize=12, pad=10)
    fig.tight_layout()
    return _save(fig, 'skills')


# ── 5. History trend line ────────────────────────────────────────────────────
def history_trend(scores, labels):
    """scores = list of floats, labels = list of short strings (dates/filenames)"""
    fig, ax = plt.subplots(figsize=(7, 3), facecolor=COLORS['bg'])
    ax.set_facecolor(COLORS['bg'])

    x = list(range(len(scores)))
    ax.plot(x, scores, color=COLORS['primary'], lw=2.5, marker='o',
            markersize=7, markerfacecolor='white', markeredgewidth=2)
    ax.fill_between(x, scores, alpha=0.12, color=COLORS['primary'])

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha='right', fontsize=8, color=COLORS['text'])
    ax.set_ylabel('ATS Score', color='#64748B', fontsize=9)
    ax.set_ylim(0, 105)
    ax.spines[['top', 'right']].set_visible(False)
    ax.spines[['left', 'bottom']].set_color('#E2E8F0')
    ax.set_title('Score History', color=COLORS['text'], fontsize=12, pad=10)
    fig.tight_layout()
    return _save(fig, 'trend')


def generate_all_charts(analysis):
    """Generate all charts and return their static paths."""
    charts = {}
    charts['gauge']    = gauge_chart(analysis['ats_score'])
    charts['subscores'] = subscores_bar(
        analysis['keyword_score'], analysis['skills_score'],
        analysis['sections_score'], analysis['format_score']
    )
    charts['keywords'] = keyword_donut(
        analysis['matched_keywords'], analysis['missing_keywords']
    )
    if analysis.get('extracted_skills'):
        charts['skills'] = skills_chart(analysis['extracted_skills'])
    return charts
