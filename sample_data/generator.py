"""
sample_data/generator.py
------------------------
Generates high-quality, authentic academic benchmark research papers in PDF format
using ReportLab. These papers directly model the "AI-Based Predictive Maintenance in Smart Manufacturing"
domain from the project specifications, complete with distinct authors, methodologies,
verifiable quantitative claims, opposing findings (contradictions), and traceable limitations.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from config import PAPERS_DIR

BENCHMARK_PAPERS = [
    {
        "filename": "paper_1_edge_ai_vibration.pdf",
        "title": "Edge-AI vs Cloud Architectures for High-Frequency Vibration Anomaly Detection in Smart Manufacturing",
        "authors": "Alex Chen, Marcus Lindqvist, Priya Sharma",
        "year": 2025,
        "abstract": (
            "Predictive maintenance in Industry 4.0 demands rapid, low-latency anomaly detection "
            "directly at the machine edge. In this paper, we benchmark an INT8 quantized 1D-CNN pipeline "
            "deployed on STM32 microcontrollers against a centralized cloud-based streaming architecture. "
            "Our edge pipeline achieves a mean inference latency of 12.4 ms with 92.1% anomaly recall on "
            "high-frequency vibration signals. However, processing continuous raw acoustic streams above 40 kHz "
            "triggers severe memory exhaustion on resource-constrained microcontrollers without downsampling. "
            "Furthermore, the reliance on single-modality 1D vibration leaves thermal expansion and optical surface "
            "wear undetected."
        ),
        "sections": [
            ("1. Introduction", (
                "Modern industrial automation relies increasingly on cyber-physical production systems. "
                "Unplanned downtime in automotive stamping and milling plants accounts for over $50 billion annually. "
                "While cloud-based machine learning offers virtually unlimited compute, high bandwidth costs, network jitter, "
                "and cloud outages make pure cloud architectures vulnerable for critical equipment protection."
            )),
            ("2. System Architecture & Edge Quantization", (
                "We developed an 8-layer temporal convolutional network with dilated kernels. Using post-training INT8 quantization "
                "with representative vibration calibration sets, the model footprint was reduced from 14.2 MB to 1.1 MB. "
                "The quantized model was flashed to an ARM Cortex-M7 microcontroller operating at 480 MHz."
            )),
            ("3. Experimental Evaluation", (
                "Benchmarking was conducted on a precision CNC spindle operating between 1,200 and 18,000 RPM. "
                "Our edge quantization pipeline delivers a 12.4 ms inference latency on STM32 microcontrollers, "
                "yielding a 92.1% anomaly recall rate while consuming only 280 mW of active power. "
                "In comparison, cloud streaming introduced an average network round-trip delay of 185 ms."
            )),
            ("4. Limitations & Open Challenges", (
                "While our edge quantization pipeline delivers a 12.4 ms inference latency on STM32 microcontrollers, "
                "it suffers from catastrophic memory exhaustion when processing continuous raw acoustic streams above 40 kHz without severe downsampling. "
                "Furthermore, the architecture operates purely on 1D accelerometer signals and completely lacks multimodal vision fusion, "
                "rendering it incapable of detecting surface micro-cracks before thermal expansion occurs. "
                "Finally, on-device test-time model adaptation remains an open problem due to backpropagation memory limits."
            )),
            ("5. Conclusion & Future Work", (
                "Edge-AI offers viable sub-15ms anomaly detection for rotational machinery. Future work must investigate "
                "lightweight multimodal sensor fusion and low-overhead temporal attention mechanisms capable of fitting within 512 KB of SRAM."
            ))
        ]
    },
    {
        "filename": "paper_2_multimodal_vision_transformer.pdf",
        "title": "Multimodal Sensor Fusion for Industrial Machinery Failure Prediction Using Vision Transformers",
        "authors": "Elena Rodriguez, Samir Patel",
        "year": 2024,
        "abstract": (
            "Relying solely on vibration waveforms often results in delayed warnings for non-rotational industrial faults. "
            "We propose ThermoVib-ViT, a multimodal cross-attention Vision Transformer that combines synchronized thermal imaging "
            "with tri-axial vibration spectrograms. Across 500 hours of accelerated life testing on industrial gearboxes, "
            "ThermoVib-ViT achieved a 96.4% F1-score, predicting catastrophic bearing seizure 6 hours earlier than vibration-only baselines. "
            "However, the model requires 45W continuous power on an Nvidia Jetson Orin, restricting practical deployment on autonomous battery-operated nodes."
        ),
        "sections": [
            ("1. Introduction", (
                "Complex manufacturing machinery undergoes degradation through both mechanical wear and thermal distress. "
                "Prior literature predominantly evaluates single-sensor configurations. We demonstrate that thermal imagery provides "
                "direct spatial heat dissipation maps that give earlier indicators of lubrication starvation than acoustic or vibration sensors alone."
            )),
            ("2. Multimodal Sensor Integration", (
                "Our experimental setup integrates a FLIR Lepton 3.5 radiometric thermal sensor (160x120 resolution) with a high-frequency "
                "piezoelectric accelerometer. We employ patch-based cross-attention where visual thermal tokens modulate vibrational frequency embeddings."
            )),
            ("3. Experimental Results", (
                "Our thermal imaging plus vibration transformer achieved a 96.4% F1-score across 500 hours of run-to-failure testing. "
                "We demonstrate that optical thermal signatures detect impending friction anomalies 6 hours earlier than vibration sensors alone. "
                "Single-modality vibration baselines only flagged anomalies 45 minutes before total seizure."
            )),
            ("4. Threats to Validity & Limitations", (
                "However, our model demands an Nvidia Jetson Orin with 45W continuous power draw, which is entirely infeasible for battery-harvested "
                "wireless sensor nodes deployed on rotating factory shafts. Moreover, the optical thermal line-of-sight is easily degraded by oil splashing "
                "and heavy dust accumulation in hostile steel mill environments, requiring frequent manual sensor cleaning."
            )),
            ("5. Conclusion", (
                "Multimodal vision-vibration fusion significantly elevates diagnostic lead time. Addressing edge power consumption and sensor lens "
                "fouling represents the critical frontier for real-world plant adoption."
            ))
        ]
    },
    {
        "filename": "paper_3_acoustic_emission_cloud.pdf",
        "title": "Empirical Evaluation of Vibration-Only Acoustic Emission for Early Bearing Wear: Cloud vs On-Premise",
        "authors": "Jan Kowalski, Sarah Jenkins, David O'Connor",
        "year": 2025,
        "abstract": (
            "The necessity of complex multimodal imaging for industrial bearing diagnosis remains disputed. In this empirical study, "
            "we evaluate high-frequency acoustic emission (100 kHz - 1 MHz) alongside 3-axis vibration across 80 industrial motors. "
            "Our findings reveal that acoustic emission provides reliable warning 48 hours prior to catastrophic failure without requiring optical cameras. "
            "We show that optical thermal cameras add minimal value in enclosed gearboxes while introducing severe maintenance issues. "
            "However, models suffer a 34.2% accuracy drop when transferred across different motor horsepower ratings."
        ),
        "sections": [
            ("1. Introduction", (
                "Several recent works argue for multimodal computer vision in predictive maintenance. We hypothesize that for enclosed machinery "
                "such as industrial pumps and planetary gearboxes, acoustic emission captures sub-surface crack propagation far earlier and at lower cost."
            )),
            ("2. Testbed & Empirical Setup", (
                "We monitored 80 induction motors ranging from 15kW to 75kW under fluctuating mechanical load profiles. "
                "Acoustic emission was captured using resonant piezoelectric sensors with cloud batch streaming."
            )),
            ("3. Findings & Comparative Analysis", (
                "Across all evaluated speed regimes, high-frequency acoustic emission and 3-axis vibration data provided sufficient early fault indicators "
                "48 hours prior to catastrophic failure; optical and thermal camera streams added negligible discriminative accuracy (<0.4% gain) while "
                "introducing severe occlusion vulnerabilities in enclosed oil-lubricated gearbox housings."
            )),
            ("4. Domain Transfer Limitations", (
                "A critical unaddressed challenge is cross-machine domain transfer: models trained on 15kW induction motors exhibited a 34.2% drop in "
                "anomaly detection accuracy when tested on 75kW compressor pumps without extensive target domain recalibration. "
                "Current supervised models fail to generalize across differing mechanical resonant frequencies and operational loads."
            )),
            ("5. Summary", (
                "Vibration and acoustic emissions remain the most practical modality for enclosed machinery. Research must focus on unsupervised domain "
                "adaptation rather than adding superfluous optical camera hardware."
            ))
        ]
    },
    {
        "filename": "paper_4_federated_predictive_maintenance.pdf",
        "title": "Federated Learning for Privacy-Preserving Fleet-Wide Predictive Maintenance Across Distributed Factories",
        "authors": "Ananya Gupta, Kenji Tanaka",
        "year": 2026,
        "abstract": (
            "Cross-enterprise collaborative model training is hindered by strict commercial confidentiality regarding production volumes and failure rates. "
            "We formulate Fed-Predict, an asynchronous federated learning framework with differential privacy for fleet-wide predictive maintenance. "
            "Across 12 simulated industrial facilities, Fed-Predict achieves 89.3% remaining useful life (RUL) estimation accuracy. "
            "However, transmitting large model checkpoints creates severe communication bottlenecks on bandwidth-limited cellular factory uplinks, "
            "and non-IID sensor distributions across distinct ambient climates induce significant client drift."
        ),
        "sections": [
            ("1. Introduction", (
                "Original Equipment Manufacturers (OEMs) seek to leverage telemetry from machines sold across worldwide client sites. "
                "Centralizing raw sensor streams exposes proprietary production cadences. Federated learning provides a mathematical guarantee of data isolation."
            )),
            ("2. Fed-Predict Architecture", (
                "Each factory trains local LSTM autoencoders on private telemetry. Local gradients are perturbed with (epsilon, delta)-differential privacy "
                "and aggregated via an asynchronous coordinate-median server."
            )),
            ("3. Experimental Evaluation", (
                "Fleet-wide federated aggregation enables multiple manufacturing plants to collaboratively train predictive maintenance models "
                "without sharing proprietary machine telemetry or operational schedules. Fed-Predict improved RUL accuracy by 14.8% over single-plant isolated models."
            )),
            ("4. Practical Bottlenecks & Open Questions", (
                "Nevertheless, the communication bandwidth required for transmitting 250MB parameter updates over industrial cellular uplinks creates "
                "severe synchronization bottlenecks. Most crucially, client non-IID data distribution remains an unsolved roadblock when machine wear rates "
                "vary across environmental temperature zones (e.g., Scandinavian vs equatorial production plants)."
            )),
            ("5. Future Directions", (
                "Federated gradient compression and personalized local meta-learning represent essential next steps to handle heterogeneous operating environments."
            ))
        ]
    },
    {
        "filename": "paper_5_tinyml_cavitation_noise.pdf",
        "title": "Ultra-Low-Power TinyML for Industrial Pump Cavitation Detection Under Extreme Acoustic Noise",
        "authors": "Wei Zhao, Fatima Al-Hassan, Carlos Mendez",
        "year": 2025,
        "abstract": (
            "Centrifugal pump cavitation causes rapid impeller erosion and catastrophic system failure in chemical processing plants. "
            "We present CavitaNet, an ultra-low-power TinyML architecture running directly on a sub-dollar ARM Cortex-M4 microcontroller. "
            "CavitaNet operates within a 42 mW power budget and achieves 91.8% detection accuracy under standard workshop conditions. "
            "However, when ambient factory floor noise exceeds 78 dB, the precision collapses to 58.1% due to static spectral filtering limits, "
            "highlighting an urgent need for adaptive on-device noise cancellation."
        ),
        "sections": [
            ("1. Introduction", (
                "Continuous acoustic monitoring of slurry and cooling pumps provides instantaneous warning of cavitation inception. "
                "Deploying tethered power cables in hazardous chemical facilities is cost-prohibitive. Self-powered TinyML vibration sensors "
                "enable ubiquitous, wireless plant retrofitting."
            )),
            ("2. TinyML Hardware & Model Pruning", (
                "We designed an ultra-compact Depthwise Separable CNN with only 24,000 parameters. Structured channel pruning and weight clustering "
                "reduced memory requirements to 48 KB RAM and 128 KB Flash."
            )),
            ("3. Experimental Results", (
                "Our INT8 quantized convolutional neural network consumes only 42 mW on an ARM Cortex-M4 core, maintaining 91.8% cavitation "
                "detection accuracy under standard workshop conditions. The device successfully ran continuously for 9 months on a primary lithium coin cell."
            )),
            ("4. Acoustic Noise Fragility", (
                "However, the classifier experiences severe false positive degradation (precision collapses to 58.1%) when ambient factory floor noise "
                "exceeds 78 dB, because the static spectral filter cannot adapt dynamically to fluctuating background interference (such as overhead cranes "
                "or adjacent diesel generators). Furthermore, zero on-device continual adaptation mechanism exists to handle mechanical aging drift."
            )),
            ("5. Concluding Remarks", (
                "Sub-50mW TinyML is technically viable for pump diagnostics. Developing adaptive edge noise cancellation and continual few-shot learning "
                "remains imperative for deployment in noisy real-world industrial environments."
            ))
        ]
    }
]

def build_pdf(paper_dict: dict, output_path: Path):
    """Render a clean, formatted 2-page academic paper PDF using ReportLab."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Academic Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        alignment=1, # Center
        textColor=colors.HexColor('#1A202C'),
        spaceAfter=8
    )
    
    author_style = ParagraphStyle(
        'DocAuthor',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        alignment=1, # Center
        textColor=colors.HexColor('#4A5568'),
        spaceAfter=4
    )
    
    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=12,
        alignment=1,
        textColor=colors.HexColor('#718096'),
        spaceAfter=14
    )
    
    abstract_heading = ParagraphStyle(
        'AbsHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        alignment=1,
        textColor=colors.HexColor('#2D3748'),
        spaceAfter=4
    )
    
    abstract_body = ParagraphStyle(
        'AbsBody',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#2D3748'),
        leftIndent=24,
        rightIndent=24,
        spaceAfter=14
    )
    
    section_heading = ParagraphStyle(
        'SecHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#1A365D'),
        spaceBefore=10,
        spaceAfter=4
    )
    
    body_style = ParagraphStyle(
        'SecBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#2D3748'),
        spaceAfter=8
    )
    
    story = []
    
    # Title & Metadata
    story.append(Paragraph(paper_dict["title"], title_style))
    story.append(Paragraph(paper_dict["authors"], author_style))
    story.append(Paragraph(f"Published: International Conference on Industrial Cyber-Physical Systems ({paper_dict['year']})", meta_style))
    
    # Abstract
    story.append(Paragraph("<b>ABSTRACT</b>", abstract_heading))
    story.append(Paragraph(paper_dict["abstract"], abstract_body))
    story.append(Spacer(1, 6))
    
    # Sections
    for i, (sec_title, sec_text) in enumerate(paper_dict["sections"]):
        # Split across pages cleanly: put Limitations and Conclusion on page 2
        if "Limitations" in sec_title or "Threats" in sec_title or "Practical Bottlenecks" in sec_title:
            story.append(PageBreak())
            
        story.append(Paragraph(sec_title, section_heading))
        story.append(Paragraph(sec_text, body_style))
        story.append(Spacer(1, 4))
        
    doc.build(story)

def generate_all_benchmark_papers():
    """Generates all 5 benchmark research PDFs into sample_data/papers/."""
    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    generated_paths = []
    for paper in BENCHMARK_PAPERS:
        pdf_path = PAPERS_DIR / paper["filename"]
        build_pdf(paper, pdf_path)
        generated_paths.append(pdf_path)
    return generated_paths

if __name__ == "__main__":
    paths = generate_all_benchmark_papers()
    print(f"Successfully generated {len(paths)} benchmark papers in {PAPERS_DIR}")
