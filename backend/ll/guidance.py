from guidance import models, select
from ll.summary import llm
from pathlib import Path

MODEL_PATH = Path.home() / ".cache/huggingface/hub/models--lmstudio-community--Meta-Llama-3-8B-Instruct-GGUF/snapshots/0910a3e69201d274d4fd68e89448114cd78e4c82/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf"

llm = models.LlamaCpp(str(MODEL_PATH), n_gpu_layers=-1, n_ctx=1024)

test_data = {'results': [ {'title': 'Lerneinheit: Das differenzierte Atommodell', 'description': 'Auf den folgenden Seiten finden Sie eine digitale Lerneinheit zur Einführung des differenzierten Atommodells. Die Einheit wurde von Mark-Tilo Schmitt im Rahmen\xa0...', 'url': 'https://uol.de/chemiedidaktik/materialien/lerneinheit-zur-einfuehrung-des-differenzierten-atommodells'}, {'title': 'Von der Teilchenvorstellung zum differenzierten Atommodell', 'description': '06.10.2017 — Als differenziertes Atommodell werden das einfache, aber sehr anschauliche, erklärungsmächtige und anschlussfähige "Kugelwolkenmodell" sowie ein\xa0...', 'url': 'https://www.chf.de/benzolring/2017/chemietage11.html'}, {'title': 'Atommodell: Übersicht, Liste, Aufbau & Erklärung | StudySmarter', 'description': '', 'url': 'https://www.studysmarter.de/schule/physik/kernphysik/atommodelle/'}, {'title': 'Rutherfordsches Atommodell - Wikipedia', 'description': '', 'url': 'https://de.wikipedia.org/wiki/Rutherfordsches_Atommodell'}, {'title': 'Atommodell nach Dalton einfach erklärt - Simpleclub', 'description': '', 'url': 'https://simpleclub.com/lessons/physik-atommodell-nach-dalton'}, {'title': 'Von DEMOKRIT zu GELL-MANN - LEIFIphysik', 'description': '', 'url': 'https://www.leifiphysik.de/kern-teilchenphysik/teilchenphysik/geschichte/von-demokrit-zu-gell-mann'}, {'title': 'Einheit für die Sekundarstufe I', 'description': 'mit dieser digitalen Lerneinheit sollt ihr euch möglichst selbstständig das, sogenannte, differenzierte Atommodell erarbeiten. Was genau hinter diesem\xa0...', 'url': 'https://uol.de/chemiedidaktik/materialien/lerneinheit-zur-einfuehrung-des-differenzierten-atommodells/einheit-fuer-die-sekundarstufe-i'}, {'title': 'Das "Kugelwolken-Modell" - Die bessere Alternative zum ...', 'description': "Üblicherweise wird zunächst das Dalton'sche Atommodell eingeführt, welches später durch das differenzierte Atommmodell von Bohr und Sommerfeld ersetzt wird.", 'url': 'https://www.friedrich-verlag.de/friedrich-plus/sekundarstufe/chemie/atombau-periodensystem/das-kugelwolken-modell-3270'}, {'title': 'Vom Dalton-Modell zum differenzierten Atommodell', 'description': 'Die Erarbeitung eines differenzierten Atommodells wie dem Energiestufenmodell oder dem Schalenmodell stellt für die Lernenden einen wichtigen Grundpfeiler\xa0...', 'url': 'https://www.springerprofessional.de/vom-dalton-modell-zum-differenzierten-atommodell/27004932'}, {'title': 'Differenziertes Atommodell', 'description': 'Differenziertes Atommodell. Wiederholung und Übung. Aufgabe: Schreibe einen Text zum Aufbau eines Atoms (z. B. Natrium-Atom) nach dem differenzierten\xa0...', 'url': 'https://naturwissenschaften.bildung-rp.de/fileadmin/_migrated/content_uploads/Kap_4_ZF_AB_Legekaertchen_Atombau.doc'}, {'title': 'Liste der Atommodelle', 'description': 'Ein Atommodell ist eine Vorstellung vom Aufbau und der Form der Atome. Schon im Altertum gab es die Atomhypothese, nach der die Atome als die unteilbaren\xa0...', 'url': 'https://de.wikipedia.org/wiki/Liste_der_Atommodelle'}, {'title': 'Atommodell: Übersicht, Liste, Aufbau & Erklärung', 'description': 'Ein Atommodell ist der Versuch, sich den Aufbau von Atomen vorzustellen. Zu den bekanntesten Modellen zählen die Atommodelle nach Demokrit, Dalton, Thomson,\xa0...', 'url': 'https://www.studysmarter.de/schule/physik/kernphysik/atommodelle/'}, {'title': 'Atommodelle in der Übersicht', 'description': 'Ein wesentlicher Unterschied zwischen dem Atommodell von Dalton und Rutherford ist, dass unterschiedliche Atommassen erklärbar sind.', 'url': 'https://www.lernort-mint.de/chemie/allgemeine-chemie/atommodelle/weiterentwicklung-der-atommodelle/'}, {'title': 'Warum gibt es unterschiedliche Atommodelle?', 'description': 'In der hier beschriebenen Unterrichtsstunde sollen die Schülerinnen und Schüler anhand der Low-Cost-Blackboxen den Prozess der Entstehung von verschiedenen\xa0...', 'url': 'https://www.friedrich-verlag.de/friedrich-plus/sekundarstufe/chemie/atombau-periodensystem/warum-gibt-es-unterschiedliche-atommodelle-11995'}]}

from guidance import models, select, gen

def get_grade_levels(snippet, model, curriculum_path="ll/phy.txt"):
    try:
        with open(curriculum_path, 'r') as f:
            curriculum = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Curriculum file not found at {curriculum_path}")
    except Exception as e:
        raise Exception(f"Error reading curriculum file: {str(e)}")
    
    prompt = f"""You are an experienced curriculum specialist. Below are the curriculum standards followed by an educational content snippet. Determine ALL appropriate grade levels where this content could be effectively used.

CURRICULUM STANDARDS:
{curriculum}

CONTENT TO ANALYZE:
"{snippet}"

Consider:
- Alignment with grade-level standards
- Vocabulary complexity
- Concept difficulty
- Required background knowledge
- Potential for differentiated instruction

First, determine if there is enough information to make a grade level assessment:
Is there sufficient information to determine grade level(s)? {select(['YES', 'NO'], name='can_determine')}

"""

    lm = model + prompt

    if lm['can_determine'] == 'NO':
        return ['UNSURE']

    lm += """
Based on the curriculum, list the most appropriate grade levels (between 5-10) where this content could be effectively used.
Selected grade levels: {"""

    # Use regex to ensure only valid grade numbers are generated
    grades = []
    while True:
        lm += gen(regex='(5|6|7|8|9|10)', name='grade', list_append=True)
        lm += select([',', '}'], name='continue')
        grades.append(set(lm['grade']))
        if lm['continue'] == '}':
            break
        
    print(grades)
    return sorted(list(set(grades)))  # Remove duplicates and sort

def classify_resource_types(snippet, model):
    """
    Classifies an educational resource snippet into one or more resource types.
    Can return multiple types or UNSURE.
    
    Args:
        snippet (str): Text snippet from an educational resource
        model: A guidance model instance
        
    Returns:
        list: The determined resource types and/or 'UNSURE'
    """
    resource_types = [
        'course', 'tutorial', 'lecture_notes', 'textbook',
        'practice_problems', 'quiz', 'video', 'podcast', 'software', 
        'image', 'simulation', 'lesson_plan', 'presentation', 
        'professional_development', 'interactive_tool', 
        'reference_material', 'lab_exercise', 'assessment', 
        'worksheet', 'study_guide'
    ]

    prompt = f"""You are an experienced educational content curator. Analyze this educational content snippet and identify ALL appropriate resource types based on its format, structure, and purpose.

Content to analyze:
"{snippet}"

Consider these characteristics:
- Format and presentation style
- Intended use cases
- Level of interactivity
- Learning objectives
- Content structure
- Assessment components

Resource Type Definitions:
- course: A structured series of lessons covering multiple topics
- tutorial: Step-by-step instructions for learning a specific concept or skill
- lecture_notes: Written summaries or outlines of classroom lectures
- textbook: Comprehensive educational material organized into chapters
- practice_problems: Collections of exercises for skill reinforcement
- quiz: Short assessment with questions to test knowledge
- video: Visual educational content
- podcast: Audio-based educational content
- software: Educational computer programs or applications
- image: Visual illustrations, diagrams, or photographs
- simulation: Interactive models demonstrating concepts
- lesson_plan: Teacher's guide for conducting a class
- presentation: Slides or visual aids for instruction
- professional_development: Materials for educator training
- interactive_tool: Hands-on digital learning resources
- reference_material: Quick-lookup resources or guides
- lab_exercise: Hands-on experimental activities
- assessment: Formal evaluation materials
- worksheet: Activity sheets for practice or review
- study_guide: Organized review materials for exam preparation

First, determine if there is enough information to classify the resource:
Is there sufficient information to determine resource type(s)? {select(['YES', 'NO'], name='can_determine')}

"""

    lm = model + prompt

    if lm['can_determine'] == 'NO':
        return ['UNSURE']

    lm += """
List ALL appropriate resource types that apply to this content.
Selected resource types: {"""

    types = []
    while True:
        lm += select(resource_types, name='type', list_append=True)
        lm += select([',', '}'], name='continue')
        types.append(lm['type'])
        if lm['continue'] == '}':
            break

    return sorted(list(set(types)))  # Remove duplicates and sort

def run():
    classifications = list()
    for result in test_data['results'][:1]:
        snippet_str = f'URL:{result["url"]}\nTitle:{result["title"]}\nDescription:{result["description"]}'
        grades = get_grade_levels(snippet_str, llm)
        resources = classify_resource_types(snippet_str, llm)
        classifications.append((snippet_str, grades, resources))

    return classifications
