"""Export functionality for analysis results."""

import io
import json
from typing import Dict, Any
from datetime import datetime


def export_markdown(result: Dict[str, Any], include_graph: bool = True) -> str:
    """Export analysis results as Markdown.

    Args:
        result: Analysis results dictionary
        include_graph: Whether to include graph description

    Returns:
        Markdown string
    """
    md = []
    
    # Header
    md.append("# Reasoning Core Analysis Report")
    md.append(f"\n*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    
    # Summary
    concepts = result.get("concepts", [])
    relationships = result.get("relationships", [])
    chains = result.get("reasoning_chains", [])
    questions = result.get("questions", [])
    
    md.append("## Summary")
    md.append(f"- **Concepts**: {len(concepts)}")
    md.append(f"- **Relationships**: {len(relationships)}")
    md.append(f"- **Reasoning Chains**: {len(chains)}")
    md.append(f"- **Questions**: {len(questions)}")
    if result.get("llm_enhanced"):
        md.append("- **LLM Enhanced**: Yes")
    md.append("")
    
    # Concepts
    if concepts:
        md.append("## Concepts")
        md.append("")
        concept_types = {}
        for concept in concepts:
            ctype = concept.get("type", "unknown")
            if ctype not in concept_types:
                concept_types[ctype] = []
            concept_types[ctype].append(concept)
        
        for ctype, type_concepts in sorted(concept_types.items()):
            md.append(f"### {ctype.title()}")
            for concept in type_concepts[:20]:  # Limit to first 20 per type
                confidence = concept.get("confidence", 0) * 100
                md.append(f"- **{concept.get('text', '')}** (confidence: {confidence:.1f}%)")
            if len(type_concepts) > 20:
                md.append(f"- *... and {len(type_concepts) - 20} more*")
            md.append("")
    
    # Relationships
    if relationships:
        md.append("## Relationships")
        md.append("")
        for rel in relationships[:50]:  # Limit to first 50
            source = rel.get("source", {})
            target = rel.get("target", {})
            rel_type = rel.get("type", "relates_to")
            source_text = source.get("text", "") if isinstance(source, dict) else str(source)
            target_text = target.get("text", "") if isinstance(target, dict) else str(target)
            md.append(f"- **{source_text}** → [{rel_type}] → **{target_text}**")
        if len(relationships) > 50:
            md.append(f"- *... and {len(relationships) - 50} more*")
        md.append("")
    
    # Reasoning Chains
    if chains:
        md.append("## Reasoning Chains")
        md.append("")
        for i, chain in enumerate(chains[:10], 1):  # Limit to first 10
            chain_type = chain.get("type", "generic")
            steps = chain.get("steps", [])
            md.append(f"### Chain {i}: {chain_type}")
            for j, step in enumerate(steps[:5], 1):  # Limit to first 5 steps
                concept = step.get("concept", {})
                action = step.get("action", "analyze")
                rationale = step.get("rationale", "")
                concept_text = concept.get("text", "") if isinstance(concept, dict) else str(concept)
                md.append(f"{j}. **{action}**: {concept_text}")
                if rationale:
                    md.append(f"   *{rationale}*")
            if len(steps) > 5:
                md.append(f"   *... and {len(steps) - 5} more steps*")
            md.append("")
    
    # Questions
    if questions:
        md.append("## Generated Questions")
        md.append("")
        for q in questions:
            md.append(f"- {q}")
        md.append("")
    
    # Knowledge Graph
    if include_graph and result.get("knowledge_graph"):
        graph = result["knowledge_graph"]
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        if nodes:
            md.append("## Knowledge Graph")
            md.append(f"- **Nodes**: {len(nodes)}")
            md.append(f"- **Edges**: {len(edges)}")
            md.append("")
            md.append("*Graph visualization available in web interface.*")
            md.append("")
    
    # Source information
    source = result.get("source")
    if source:
        md.append("## Source Information")
        md.append(f"- **Type**: {source.get('type', 'unknown')}")
        if source.get("filename"):
            md.append(f"- **File**: {source['filename']}")
        if source.get("url"):
            md.append(f"- **URL**: {source['url']}")
        md.append("")
    
    return "\n".join(md)


def export_pdf(result: Dict[str, Any]) -> bytes:
    """Export analysis results as PDF.

    Args:
        result: Analysis results dictionary

    Returns:
        PDF bytes

    Note:
        Requires reportlab: pip install reportlab
    """
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib import colors
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        raise ImportError("reportlab is required for PDF export. Install with: pip install reportlab")
    
    # Create PDF buffer
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=30,
    )
    
    # Story (content)
    story = []
    
    # Title
    story.append(Paragraph("Reasoning Core Analysis Report", title_style))
    story.append(Paragraph(f"<i>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Summary
    concepts = result.get("concepts", [])
    relationships = result.get("relationships", [])
    chains = result.get("reasoning_chains", [])
    questions = result.get("questions", [])
    
    summary_data = [
        ["Metric", "Count"],
        ["Concepts", str(len(concepts))],
        ["Relationships", str(len(relationships))],
        ["Reasoning Chains", str(len(chains))],
        ["Questions", str(len(questions))],
    ]
    if result.get("llm_enhanced"):
        summary_data.append(["LLM Enhanced", "Yes"])
    
    summary_table = Table(summary_data, colWidths=[2*inch, 1*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    story.append(Paragraph("<b>Summary</b>", styles['Heading2']))
    story.append(summary_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Concepts
    if concepts:
        story.append(Paragraph("<b>Concepts</b>", styles['Heading2']))
        concept_data = [["Concept", "Type", "Confidence"]]
        
        # Group by type
        concept_types = {}
        for concept in concepts:
            ctype = concept.get("type", "unknown")
            if ctype not in concept_types:
                concept_types[ctype] = []
            concept_types[ctype].append(concept)
        
        for ctype, type_concepts in sorted(concept_types.items()):
            for concept in type_concepts[:15]:  # Limit per type
                confidence = concept.get("confidence", 0) * 100
                concept_data.append([
                    concept.get("text", ""),
                    ctype,
                    f"{confidence:.1f}%",
                ])
        
        if len(concept_data) > 1:
            concepts_table = Table(concept_data, colWidths=[3*inch, 1.5*inch, 1*inch])
            concepts_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
            ]))
            story.append(concepts_table)
        story.append(Spacer(1, 0.2*inch))
    
    # Relationships
    if relationships:
        story.append(Paragraph("<b>Relationships</b>", styles['Heading2']))
        for rel in relationships[:30]:  # Limit to first 30
            source = rel.get("source", {})
            target = rel.get("target", {})
            rel_type = rel.get("type", "relates_to")
            source_text = source.get("text", "") if isinstance(source, dict) else str(source)
            target_text = target.get("text", "") if isinstance(target, dict) else str(target)
            story.append(Paragraph(f"<b>{source_text}</b> → [{rel_type}] → <b>{target_text}</b>", styles['Normal']))
        if len(relationships) > 30:
            story.append(Paragraph(f"<i>... and {len(relationships) - 30} more relationships</i>", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
    
    # Questions
    if questions:
        story.append(Paragraph("<b>Generated Questions</b>", styles['Heading2']))
        for q in questions:
            story.append(Paragraph(f"• {q}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def export_html(result: Dict[str, Any]) -> str:
    """Export analysis results as HTML.

    Args:
        result: Analysis results dictionary

    Returns:
        HTML string
    """
    html = []
    
    html.append("<!DOCTYPE html>")
    html.append("<html><head>")
    html.append('<meta charset="UTF-8">')
    html.append('<title>Reasoning Core Analysis Report</title>')
    html.append('<style>')
    html.append('body { font-family: Arial, sans-serif; margin: 40px; }')
    html.append('h1 { color: #1e40af; }')
    html.append('h2 { color: #3b82f6; margin-top: 30px; }')
    html.append('table { border-collapse: collapse; width: 100%; margin: 20px 0; }')
    html.append('th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }')
    html.append('th { background-color: #3b82f6; color: white; }')
    html.append('tr:nth-child(even) { background-color: #f3f4f6; }')
    html.append('.concept-item { margin: 5px 0; }')
    html.append('.relationship { margin: 10px 0; padding: 10px; background: #f9fafb; border-left: 3px solid #3b82f6; }')
    html.append('</style>')
    html.append("</head><body>")
    
    html.append("<h1>🧠 Reasoning Core Analysis Report</h1>")
    html.append(f"<p><em>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>")
    
    # Summary
    concepts = result.get("concepts", [])
    relationships = result.get("relationships", [])
    chains = result.get("reasoning_chains", [])
    questions = result.get("questions", [])
    
    html.append("<h2>Summary</h2>")
    html.append("<table>")
    html.append("<tr><th>Metric</th><th>Count</th></tr>")
    html.append(f"<tr><td>Concepts</td><td>{len(concepts)}</td></tr>")
    html.append(f"<tr><td>Relationships</td><td>{len(relationships)}</td></tr>")
    html.append(f"<tr><td>Reasoning Chains</td><td>{len(chains)}</td></tr>")
    html.append(f"<tr><td>Questions</td><td>{len(questions)}</td></tr>")
    if result.get("llm_enhanced"):
        html.append("<tr><td>LLM Enhanced</td><td>Yes</td></tr>")
    html.append("</table>")
    
    # Concepts
    if concepts:
        html.append("<h2>Concepts</h2>")
        html.append("<table>")
        html.append("<tr><th>Concept</th><th>Type</th><th>Confidence</th></tr>")
        for concept in concepts[:100]:  # Limit to first 100
            confidence = concept.get("confidence", 0) * 100
            html.append(f"<tr>")
            html.append(f"<td>{concept.get('text', '')}</td>")
            html.append(f"<td>{concept.get('type', 'unknown')}</td>")
            html.append(f"<td>{confidence:.1f}%</td>")
            html.append(f"</tr>")
        html.append("</table>")
    
    # Relationships
    if relationships:
        html.append("<h2>Relationships</h2>")
        for rel in relationships[:50]:  # Limit to first 50
            source = rel.get("source", {})
            target = rel.get("target", {})
            rel_type = rel.get("type", "relates_to")
            source_text = source.get("text", "") if isinstance(source, dict) else str(source)
            target_text = target.get("text", "") if isinstance(target, dict) else str(target)
            html.append(f'<div class="relationship">')
            html.append(f"<strong>{source_text}</strong> → [{rel_type}] → <strong>{target_text}</strong>")
            html.append("</div>")
    
    # Questions
    if questions:
        html.append("<h2>Generated Questions</h2>")
        html.append("<ul>")
        for q in questions:
            html.append(f"<li>{q}</li>")
        html.append("</ul>")
    
    html.append("</body></html>")
    
    return "\n".join(html)
