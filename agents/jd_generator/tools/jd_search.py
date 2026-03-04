"""
JD Search tool -- Mocked RAG search for similar past job descriptions.
"""

from langchain_core.tools import tool


@tool
def jd_search(job_title: str, department: str | None = None) -> dict:
    """Searches for similar past job descriptions via RAG to use as references
    when composing a new JD."""
    return run_jd_search(job_title, department)


def run_jd_search(job_title: str, department: str | None = None) -> dict:
    """Actual implementation -- returns mock similar JDs."""
    if not job_title or not isinstance(job_title, str):
        return {"success": False, "error": "job_title is required and must be a non-empty string."}

    return {
        "success": True,
        "error": None,
        "count": 5,
        "similar_jds": [
            {
                "id": "JD-2024-001",
                "title": "Senior Data Scientist",
                "department": department or "Technology",
                "level": "Vice President",
                "similarity_score": 0.89,
                "summary": "Lead a team of data scientists building ML models for risk analytics.",
                "sections": {
                    "your_team": "Join our risk analytics group, a team of 5-8 data scientists building ML models that power firm-wide risk decisions. We work at the intersection of quantitative research and engineering to deliver real-time risk insights to trading desks and senior leadership. Our team culture values intellectual curiosity, rigorous experimentation, and collaborative problem-solving.",
                    "your_role": "- Lead a team of 5-8 data scientists\n- Design and implement ML models for risk analytics\n- Collaborate with stakeholders to define requirements and success metrics\n- Mentor junior team members and conduct code reviews\n- Present findings to senior leadership and business partners\n- Drive adoption of best practices in model development and deployment",
                    "your_expertise": "- 8+ years of experience in data science or quantitative research\n- PhD or MS in Computer Science, Statistics, or related field\n- Strong experience with Python, TensorFlow, PyTorch\n- Experience leading technical teams\n- Deep understanding of statistical modeling and machine learning\n- Excellent communication and presentation skills"
                }
            },
            {
                "id": "JD-2024-002",
                "title": "AI/ML Engineering Lead",
                "department": department or "Technology",
                "level": "Executive Director",
                "similarity_score": 0.82,
                "summary": "Drive the development of AI/ML infrastructure and lead engineering team.",
                "sections": {
                    "your_team": "Our AI/ML engineering team of 10+ engineers is building the next-generation AI platform that powers intelligent solutions across the firm. We operate in a fast-paced, innovation-driven environment where engineers have the autonomy to experiment with cutting-edge technologies and the responsibility to deliver production-grade systems.",
                    "your_role": "- Architect and build scalable ML infrastructure\n- Lead a team of 10+ engineers across multiple workstreams\n- Define technical roadmap and drive execution\n- Partner with product teams on AI features\n- Establish engineering standards and best practices\n- Manage vendor relationships and technology evaluations",
                    "your_expertise": "- 10+ years in software engineering, 5+ in ML\n- Experience with cloud platforms (AWS/Azure/GCP)\n- Strong leadership and communication skills\n- Track record of delivering ML systems at scale\n- Experience with MLOps, model monitoring, and CI/CD pipelines\n- Familiarity with large language models and generative AI"
                }
            },
            {
                "id": "JD-2024-003",
                "title": "ML Platform Engineer",
                "department": department or "Technology",
                "level": "Vice President",
                "similarity_score": 0.78,
                "summary": "Build and maintain the firm's ML platform for model training and serving.",
                "sections": {
                    "your_team": "The ML Platform team is a dedicated group of 6 engineers responsible for building and operating the firm's centralized machine learning infrastructure. We enable data scientists and ML engineers across the organization to train, deploy, and monitor models at scale with minimal friction.",
                    "your_role": "- Design and build ML platform components (feature store, model registry, serving layer)\n- Develop self-service tools for data scientists to train and deploy models\n- Optimize training pipelines for cost and performance\n- Implement monitoring and alerting for model performance drift\n- Collaborate with infrastructure teams on compute resource management\n- Support platform users and drive adoption across teams",
                    "your_expertise": "- 7+ years in software engineering with focus on distributed systems\n- Strong experience with Kubernetes, Docker, and cloud-native architectures\n- Hands-on experience with ML frameworks (PyTorch, TensorFlow, Ray)\n- Proficiency in Python and Go or Java\n- Experience building developer tools and platform services\n- Understanding of ML lifecycle from experimentation to production"
                }
            },
            {
                "id": "JD-2024-004",
                "title": "NLP Research Scientist",
                "department": department or "Technology",
                "level": "Vice President",
                "similarity_score": 0.74,
                "summary": "Conduct NLP research and develop language-based AI solutions for the firm.",
                "sections": {
                    "your_team": "Our Applied NLP Research group is a specialized team of 4 research scientists focused on advancing the firm's natural language processing capabilities. We tackle challenges ranging from document understanding and information extraction to conversational AI and semantic search, publishing our findings at top-tier venues.",
                    "your_role": "- Conduct research in NLP and large language models\n- Develop novel approaches for document understanding and text analytics\n- Fine-tune and evaluate LLMs for domain-specific applications\n- Collaborate with engineering teams to productionize research prototypes\n- Publish findings at top NLP/AI conferences\n- Stay current with the latest advances in NLP and generative AI",
                    "your_expertise": "- PhD in Computer Science, Computational Linguistics, or related field\n- 5+ years of research experience in NLP or related areas\n- Strong publication record at venues such as ACL, EMNLP, NeurIPS\n- Deep expertise with transformer architectures and LLM fine-tuning\n- Proficiency in Python and deep learning frameworks\n- Experience transitioning research prototypes to production systems"
                }
            },
            {
                "id": "JD-2024-005",
                "title": "Data Engineering Lead",
                "department": department or "Technology",
                "level": "Vice President",
                "similarity_score": 0.71,
                "summary": "Lead the data engineering team building pipelines that power analytics and ML.",
                "sections": {
                    "your_team": "The Data Engineering team consists of 8 engineers building the data infrastructure that underpins analytics, reporting, and machine learning across the firm. We manage petabyte-scale data pipelines and are modernizing our stack to support real-time streaming and self-service data access for hundreds of internal users.",
                    "your_role": "- Lead a team of 8 data engineers across ETL and streaming workstreams\n- Design and build scalable data pipelines for analytics and ML use cases\n- Define data architecture standards and governance practices\n- Partner with data science and analytics teams on data requirements\n- Drive migration from legacy batch systems to modern streaming architectures\n- Ensure data quality, reliability, and compliance with regulatory requirements",
                    "your_expertise": "- 8+ years in data engineering or related roles\n- Strong experience with Spark, Kafka, Airflow, and cloud data services\n- Proficiency in SQL and Python\n- Experience leading engineering teams\n- Knowledge of data governance, lineage, and quality frameworks\n- Familiarity with ML data requirements (feature engineering, training data management)"
                }
            }
        ]
    }
