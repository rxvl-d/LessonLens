# LessonLens

LessonLens is a browser extension that augments web search interfaces with AI-powered features to help teachers find educational resources more effectively.

This repository contains the code for both the browser extension and the backend service that powers it.

## About

This extension supports the paper "Supporting Teachers through AI-augmented Web Search for Educational Resource Discovery" by Ratan J. Sebastian and Anett Hoppe from L3S Research Center, Leibniz University Hannover and TIB – Leibniz Information Centre for Science and Technology in Germany.

The extension is designed to help teachers find and evaluate educational resources online by providing educationally relevant information directly within search engine results pages.

## Key Features

1. **SERP Overview** - A visualization showing characteristics of search results, including educational level and access type
2. **Metadata Summaries** - Structured educational metadata to enable quick filtering of resources
3. **Task Summaries** - Q&A style summaries tailored to the search context to support pedagogical assessment

## Repository Structure

- `extension/` - Browser extension code (TypeScript)
- `backend/` - Backend service code (Python)
- `data/` - Study data and model training data

## Research Findings

The authors found three key guidelines for AI-assisted educational resource discovery:

1. Interfaces should support a two-stage decision process (quick metadata filtering followed by detailed pedagogical assessment)
2. Simple visualizations with confidence indicators work better than complex displays
3. Interfaces must support customization as teachers have different evaluation approaches

## Installation

See the extension directory for build and installation instructions.

## Citation

If you use this code or reference the project, please cite:

```
Sebastian, R. J., & Hoppe, A. (2023). Supporting Teachers through AI-augmented Web Search for Educational Resource Discovery. [Journal/Conference details]
```