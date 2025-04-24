# VecApp AI Service

## Overview
VecApp AI Analytics Service is a sophisticated system designed to analyze and summarize follow-up interactions with church visitors. The service processes both structured and unstructured data from the Church Management System (CHMS) to provide comprehensive insights into visitor engagement, decisions, and follow-up effectiveness.

## Features

### 1. AI-Powered Follow-up Analysis
- Processes visitor data from CHMS
- Analyzes structured and unstructured follow-up notes
- Tracks individual and family engagement
- Generates comprehensive follow-up summary reports

### 2. Data Processing Capabilities
- Structured data analysis from First Timer forms and Feedback Forms
- Unstructured data analysis using NLP for:
  - Feedbacks
  - Prayer Requests
  - Follow-up Notes
- Family structure correlation
- Visitor engagement tracking

### 3. Report Generation
- PDF report generation with sections for:
  - Visitor Summary
  - Engagement Breakdown
  - Follow-up Outcomes & Decision Trends
  - Individual/Family Notes Summary
  - AI-driven Recommendations

## Technical Stack

- **Backend**: Python/FastAPI
- **Database**: PostgreSQL
- **Cache**: Redis
- **Infrastructure**: Kubernetes
- **Monitoring**: OpenTelemetry
- **Additional Services**:
  - NLP Service
  - PDF Generation Service

## Getting Started

### Prerequisites
- Python 3.8+
- Docker
- Kubernetes cluster
- PostgreSQL database
- Redis instance

### Installation

1. Clone the repository:
```bash
git clone https://github.com/idaf-ai/vecap-ai.git
cd vecap-ai
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Running Locally

1. Start the development server:
```bash
uvicorn main:app --reload
```

2. Access the API documentation: 
```

### Deployment

Deploy to Kubernetes using the provided configuration:

```bash
kubectl apply -f k8s/analytics-deployment.yaml
```

## API Endpoints

### Analytics API
- `GET /api/v1/analytics/dashboard` - Get main dashboard metrics
- `GET /api/v1/analytics/visitor-trends` - Get visitor engagement trends
- `GET /api/v1/analytics/volunteer-performance` - Get volunteer performance metrics

## Performance Requirements

- Report generation within 30 seconds for standard date ranges
- Handles up to 10,000 visitor records per report
- 99.9% system uptime
- Secure data transmission over HTTPS
- Role-based access control (RBAC)

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Security

- All reports are encrypted at rest
- HTTPS-only communication
- Role-based access control
- Audit logging for report generation and access

## License

This project is proprietary and confidential. Unauthorized copying, modification, distribution, or use of this software is strictly prohibited.

## Support

For support, please contact the development team or create an issue in the repository.