# 📌 Indeed RPA Lifecycle Automation

## 🧾 Project Overview

This project automates the full lifecycle management of job postings on the **Indeed Employer platform** using Python automation.

It handles both **closing outdated listings** and **posting new listings** in a scheduled and automated workflow.

---

## 🎯 Project Purpose

The system was built to solve several issues in manual job management:

### ⏱️ Time Inefficiency
Managing 15+ job postings manually per cycle (1st & 16th of each month) takes several hours.

### ⚠️ Human Error
Manual handling increases the risk of:
- Incorrect URL copying
- Wrong job template selection

### 📉 Listing Performance
Indeed prioritizes fresh job postings. This system ensures listings are consistently refreshed.

### 🔐 Security Complexity
Indeed uses strict Cloudflare protection. This system uses Python automation with Playwright to simulate human-like behavior for reliable execution.

---

## 🏗️ System Architecture

The system is divided into two main modules:

---

## 🧹 Module 1: Auto_Close_iffix.py (Termination Phase)

### Purpose
Closes outdated job listings that have reached their lifecycle limit (15 days).

### Features
- Reads job status from Excel
- Detects “Open” listings
- Executes automated 6-step closing process

### Output
- ✅ Success (closed listing)
- ⏭️ Skipped (already closed)

---

## 🚀 Module 2: Auto_Post&GetLink.py (Creation & Sync Phase)

### Purpose
Creates new job postings and synchronizes generated links into the database.

### Features

#### 📄 Template-Based Posting
- Reads job titles from Excel
- Selects appropriate Indeed templates
- Ensures consistent job descriptions

#### 🔗 Dynamic Link Capture
- Waits for Indeed to generate job URL
- Captures the unique job link
- Writes back into Excel (Sheet2)

#### 📢 Real-Time Reporting
- Sends job links to WhatsApp group via webhook
- Enables real-time monitoring without dashboard access

---

## 💼 Business Impact

### 📊 Data Centralization
Excel acts as a live database with automatically updated job links.

### 🔄 Operational Consistency
Scheduled execution:
- 11:00 AM → Close jobs  
- 11:30 AM → Post jobs  
(1st and 16th of every month)

### 🛡️ Security Compliance
Uses persistent browser sessions to reduce detection risk and simulate human-like behavior.

---

## ⚙️ Tech Stack

- Python  
- Playwright (browser automation)  
- Excel (data storage)  
- Webhook integration (WhatsApp notifications)  
- Scheduler (cron / task scheduling)

---

## 📌 Workflow Summary

Excel → Close Old Listings → Post New Listings → Capture URLs → Update Excel → Send Notifications

---

## 🚀 Result

This system improves:
- Efficiency ⏱️  
- Accuracy 🎯  
- Consistency 🔄  
- Real-time visibility 📡  

---

## 👨‍💻 Author

Created by: **intern 656@automattor.com**