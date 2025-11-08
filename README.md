# HydrAid
HydrAid is a lightweight app built with Pygame, Meta Llama and Open Street Maps, which aims to improve healthcare access and familiarity to everyone through easily accessible UI. HydrAid includes three main features: amenity lookup; daily tasks, a personalised AI Health Chatbot. 

## Amenity Lookup
The amenity lookup feature uses the free OpenStreetMap API to show nearby hospitals, water points, clinics, and food shelters within a 5000 metre radius. It includes a built-in city-to-coordinate system that accepts both city names and GPS inputs, increasing accessibility. A dropdown menu and scrollable results make the interface clean and easy to use. This supports SDGs 3 and 6 by improving access to local health, sanitation, and water services. The rate-limited API and lightweight design make it technically feasible and reliable.

## Daily Tasks
The daily tasks section uses the Meta Llama API (via Hugging Face) to generate short, motivational daily health and sustainability tasks stored locally in a JSON cache. The creative use of AI for personalised wellbeing goals promotes real-world action towards SDGs 2, 3, and 6. Its simplicity, local caching, and cloud-hosted model make it efficient, smooth on low-end devices, and easy to maintain.

## AI Chatbot
The chatbot gives personalised, awareness-based health guidance without offering diagnoses. It connects to the Amenity Lookup, suggesting when to seek medical care. Built using the same free Meta Llama API, it also provides multi-language support, increasing feasibility. This feature creatively promotes self-care and informed decision-making, supporting global health access. Its minimal, intuitive UI ensures accessibility for all users while keeping performance feasible for a solo developer.
