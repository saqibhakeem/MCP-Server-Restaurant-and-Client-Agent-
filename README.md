# 🍽️ Restaurant AI Assistant: MCP Server & Client

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Model Context Protocol](https://img.shields.io/badge/MCP-1.3.0+-8A2BE2?style=flat)](https://modelcontextprotocol.io/)
[![Groq](https://img.shields.io/badge/Groq-Fast%20Inference-F05A28?style=flat)](https://groq.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An end-to-end implementation of the **Model Context Protocol (MCP)** demonstrating an autonomous Restaurant Management & Reservation system ("L'Aura Bistro"). This repository contains:

1. **MCP Server** (`server.py`): Exposes restaurant inquiry, table availability, reservation, and cancellation capabilities as standardized MCP tools over modern HTTP transports.
2. **MCP Client** (`client.py`): A Python script showing how to programmatically connect to the MCP server, discover tools, and invoke them via SSE (Server-Sent Events).
3. **Autonomous Groq AI Agent** (`agent.py`): An intelligent CLI agent powered by Groq's high-speed LLM inference. It dynamically fetches MCP tool definitions, transforms schemas into function-calling specs, and executes multi-step workflows (e.g., browsing the menu, checking slots, and booking tables).

---

## 📑 Table of Contents

- [Architecture Overview](#-architecture-overview)
- [Key Features](#-key-features)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
- [Usage Guide](#-usage-guide)
  - [1. Starting the MCP Server](#1-starting-the-mcp-server)
  - [2. Testing with the Direct Client](#2-testing-with-the-direct-client)
  - [3. Running the Autonomous AI Agent](#3-running-the-autonomous-ai-agent)
- [MCP Tools Reference](#-mcp-tools-reference)
- [Data Storage Schema](#-data-storage-schema)
- [Troubleshooting & FAQs](#-troubleshooting--faqs)
- [License](#-license)

---

## 🏛 Architecture Overview

The system bridges conversational AI with deterministic business logic and file-based state using the standard Model Context Protocol:

```mermaid
flowchart TD
    subgraph User Interaction
        U[User CLI / Prompt]
    end

    subgraph Autonomous AI Agent (agent.py)
        A[GroqMCPAgent]
        LLM[Groq LLM / Chat Completions]
        TC[Tool Schema Transformer & Dispatcher]
    end

    subgraph Direct Client (client.py)
        C[MCP ClientSession / SSE Client]
    end

    subgraph MCP Transport Layer
        direction TB
        T1[Streamable HTTP / MCP POST]
        T2[Server-Sent Events / SSE]
    end

    subgraph Restaurant MCP Server (server.py)
        S[MCPServer: RestaurantService]
        subgraph Tools
            T_Info[get_restaurant_info]
            T_Menu[get_menu]
            T_Avail[check_available_tables]
            T_Book[book_table]
            T_Det[get_booking_details]
            T_Cancel[cancel_booking]
        end
    end

    subgraph Persistence Layer (JSON)
        D_Menu[(menu.json)]
        D_Tables[(tables.json)]
        D_Bookings[(bookings.json)]
    end

    U --> A
    A <--> LLM
    A --> TC
    TC --> T1
    C --> T2
    T1 --> S
    T2 --> S
    S --> Tools
    Tools <--> D_Menu
    Tools <--> D_Tables
    Tools <--> D_Bookings
```

---

## ✨ Key Features

- **Standardized MCP Implementation**: Built using the official Python [`mcp`](https://github.com/modelcontextprotocol/python-sdk) library.
- **Multiple Transport Support**:
  - `streamable-http`: Modern streaming HTTP transport for fast, multiplexed communication.
  - `sse`: Traditional Server-Sent Events transport.
- **Dynamic Tool Schema Translation**: Automatically maps MCP JSON schemas (`inputSchema`) to OpenAI/Groq function calling format.
- **Multi-Server Aggregation**: The AI agent can connect to multiple MCP servers concurrently (e.g. local and remote ngrok endpoints) and dispatch commands to the corresponding server session.
- **Autonomous Tool-Calling Loop**: Handles chained tool executions (e.g., checking restaurant hours $\rightarrow$ filtering vegetarian dishes $\rightarrow$ checking available tables $\rightarrow$ confirming booking).
- **Lightweight File-Based Persistence**: Zero database configuration needed; records are persisted with auto-generated identifiers in JSON format.

---

## 📂 Project Structure

```text
.
├── .env                  # Environment variables (API keys)
├── .env.example          # Sample environment template
├── requirements.txt      # Python dependencies
├── server.py             # FastMCP / MCPServer implementation
├── client.py             # Basic programmatic MCP client example
├── agent.py              # Autonomous CLI chat agent with Groq & MCP integration
└── data/
    ├── menu.json         # Restaurant menu items, categories, and dietary tags
    ├── tables.json       # Table layout, capacities, and locations
    └── bookings.json     # Active and cancelled reservation records
```

---

## ⚙️ Prerequisites

- **Python**: Version `3.10` or higher
- **Groq API Key**: Obtain a free API key from [Groq Console](https://console.groq.com/) for running the intelligent agent (`agent.py`).

---

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/mcp-restaurant-system.git
cd mcp-restaurant-system
```

### 2. Set Up a Virtual Environment

```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

Install the base requirements plus the agent dependencies:

```bash
pip install -r requirements.txt
pip install groq python-dotenv
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```ini
GROQ_API_KEY="your-groq-api-key-here"
```

---

## 💻 Usage Guide

### 1. Starting the MCP Server

The server provides all restaurant tools over HTTP (defaults to `0.0.0.0:8000`).

```bash
python server.py
```

*Note: Depending on your MCP SDK version, the server operates with `streamable-http` or `sse` transport.*

---

### 2. Testing with the Direct Client

To run a scripted test verifying tool discovery, menu queries, and reservation bookings:

```bash
python client.py
```

**Sample Output:**
```text
Available Tools: ['get_restaurant_info', 'get_menu', 'check_available_tables', 'book_table', 'get_booking_details', 'cancel_booking']

Menu Results:
[
  {
    "id": "M04",
    "name": "Wild Mushroom Tagliatelle",
    "category": "main",
    "price": 24.0,
    "description": "Handmade pasta with porchini, chanterelles, and aged parmesan.",
    "dietary": ["vegetarian"],
    "available": true
  }
]

Booking Confirmation:
{
  "status": "confirmed",
  "booking_id": "BK-A8B9C0",
  "table_id": "T1",
  "location": "indoor",
  "date": "2026-11-15",
  "time_slot": "19:30",
  "party_size": 2,
  "message": "Table reserved successfully under Sarah Connor."
}
```

---

### 3. Running the Autonomous AI Agent

Launch the interactive conversational agent using Groq's LLM:

```bash
# Connect to local MCP server
python agent.py --servers http://localhost:8000/mcp

# Or connect to an SSE endpoint
python agent.py --servers http://localhost:8000/sse

# Optionally specify a Groq model (e.g., openai/gpt-oss-120b, llama-3.3-70b-versatile)
python agent.py --servers http://localhost:8000/mcp --model openai/gpt-oss-120b
```

#### Example Agent Conversations

**Example 1: Menu Consultation & Dietary Filtering**
> **User:** What vegetarian options do you have for dinner?  
> **Agent:** *(Calls `get_menu(category="main", dietary_tag="vegetarian")`)*  
> We have the **Wild Mushroom Tagliatelle** ($24.00), made with handmade pasta, porchini, chanterelles, and aged parmesan. We also have **Truffle Arancini** ($14.50) as an appetizer and **Dark Chocolate Fondant** ($11.00) for dessert!

**Example 2: Table Availability & Booking**
> **User:** I want to book a table for 4 people on 2026-11-20 at 19:30. My name is Alex, phone is 555-0144.  
> **Agent:** *(Calls `check_available_tables` $\rightarrow$ `book_table`)*  
> Your table has been reserved successfully!  
> - **Booking ID:** `BK-3F12A8`  
> - **Name:** Alex  
> - **Party Size:** 4  
> - **Date & Time:** November 20, 2026 at 19:30  
> - **Table Location:** Window  

**Example 3: Checking or Canceling Reservations**
> **User:** Can you cancel my booking BK-3F12A8?  
> **Agent:** *(Calls `cancel_booking(booking_id="BK-3F12A8")`)*  
> Your booking `BK-3F12A8` has been cancelled successfully. Let me know if you need any further assistance!

---

## 🛠 MCP Tools Reference

| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| `get_restaurant_info` | *None* | Returns restaurant hours, address, phone number, cancellation policy, and valid booking time slots. |
| `get_menu` | `category` *(str, optional)*,<br>`dietary_tag` *(str, optional)* | Retrieves available menu items. Filters by category (`appetizer`, `main`, `dessert`) and dietary preference (`vegetarian`, `gluten-free`). |
| `check_available_tables` | `date` *(YYYY-MM-DD)*,<br>`time_slot` *(HH:MM)*,<br>`party_size` *(int)* | Searches for unreserved tables with sufficient capacity for the party. |
| `book_table` | `customer_name` *(str)*,<br>`customer_phone` *(str)*,<br>`party_size` *(int)*,<br>`date` *(YYYY-MM-DD)*,<br>`time_slot` *(HH:MM)*,<br>`special_requests` *(str)* | Validates date and availability, selects the most capacity-efficient table, and saves the booking. |
| `get_booking_details` | `booking_id` *(str)* | Retrieves current status (`confirmed`/`cancelled`), table assignment, and details for a given booking ID. |
| `cancel_booking` | `booking_id` *(str)* | Updates reservation status to `cancelled` and records the cancellation timestamp. |

---

## 🗄️ Data Storage Schema

All data files reside in the [`data/`](file:///d:/Python%20For%20AI%20NASTP%20DSTP/Projects/MCP%20Server%20And%20Client/data) directory:

- **`menu.json`**:
  ```json
  {
    "id": "M01",
    "name": "Truffle Arancini",
    "category": "appetizer",
    "price": 14.50,
    "description": "Crispy risotto balls filled with wild mushrooms and truffle aioli.",
    "dietary": ["vegetarian"],
    "available": true
  }
  ```
- **`tables.json`**:
  ```json
  {
    "table_id": "T1",
    "capacity": 2,
    "location": "indoor"
  }
  ```
- **`bookings.json`**:
  ```json
  {
    "booking_id": "BK-F3F958",
    "table_id": "T1",
    "customer_name": "Sarah Connor",
    "customer_phone": "+1-555-894-1122",
    "party_size": 2,
    "date": "2026-11-15",
    "time_slot": "19:30",
    "location": "indoor",
    "special_requests": "Window table preferred",
    "status": "confirmed",
    "created_at": "2026-11-06T16:57:39.066018"
  }
  ```

---

## ❓ Troubleshooting & FAQs

### 1. Connection Refused / Connection Aborted
- Ensure the server is actively running (`python server.py`) before starting `client.py` or `agent.py`.
- Verify the server address and port (default: `http://localhost:8000`). If using a remote tunnel (such as ngrok), pass the full HTTPS URL using `--servers`.

### 2. Transport Protocol Mismatch (`sse` vs `streamable-http`)
- In `server.py`, `mcp.run()` uses `transport="streamable-http"` (or `transport="sse"` in older MCP releases).
- `agent.py` automatically distinguishes between endpoints:
  - URLs ending with `/sse` use `sse_client`.
  - All other URLs use `streamable_http_client`.

### 3. Missing Groq API Key
- If `agent.py` reports authentication errors, make sure you created a `.env` file containing `GROQ_API_KEY="your-key"` and that `python-dotenv` is installed.

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
