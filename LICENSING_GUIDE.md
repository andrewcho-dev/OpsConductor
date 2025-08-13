# OpsConductor Licensing Guide

## 📋 Overview

This document provides comprehensive guidance on the licensing requirements for OpsConductor and its third-party dependencies.

## 🏷️ Primary License: MIT

OpsConductor is licensed under the **MIT License**, which provides:

### ✅ Permissions
- ✅ **Commercial use** - Use in commercial applications
- ✅ **Modification** - Modify the source code
- ✅ **Distribution** - Distribute copies of the software
- ✅ **Private use** - Use privately without disclosure
- ✅ **Sublicensing** - Grant sublicenses to third parties

### 📋 Conditions
- 📋 **License and copyright notice** - Include the original license and copyright notice

### ❌ Limitations
- ❌ **No liability** - Software is provided "as is"
- ❌ **No warranty** - No warranty is provided

## 🔍 Third-Party Dependencies Analysis

### 🟢 MIT Licensed Components (No Special Requirements)
- **FastAPI** - Web framework
- **React** - Frontend framework
- **Material-UI** - UI component library
- **SQLAlchemy** - Database ORM
- **Redis** - Caching library
- **Chart.js** - Charting library
- **Axios** - HTTP client
- **Most Python/JavaScript dependencies**

### 🟡 LGPL Licensed Components (Special Handling Required)

#### Paramiko (LGPL v2.1)
**What it does**: SSH client library for Python
**License requirements**:
- ✅ **Can be used** in proprietary software
- ✅ **No source disclosure** required for your code
- ⚠️ **Must provide LGPL notice** (included in NOTICE file)
- ⚠️ **Users must be able to replace** the LGPL library

**Compliance**: ✅ **Fully compliant** - NOTICE file includes required attribution

### 🟢 BSD Licensed Components (Permissive)
- **PostgreSQL** - Database (PostgreSQL License - BSD-style)
- **Nginx** - Web server (BSD-2-Clause)
- **Celery** - Task queue (BSD)

### 🟢 Apache 2.0 Licensed Components (Permissive)
- **Docker** - Containerization platform
- **Prometheus** - Monitoring system
- **Grafana** - Visualization platform

## 📄 Required Files

### 1. LICENSE File ✅
- **Location**: `/LICENSE`
- **Content**: MIT License text with OpsConductor copyright
- **Purpose**: Primary license for your original code

### 2. NOTICE File ✅
- **Location**: `/NOTICE`
- **Content**: Third-party attributions and license notices
- **Purpose**: Legal compliance for third-party components

### 3. README License Section ✅
- **Location**: `/README.md`
- **Content**: License information and links to LICENSE/NOTICE files
- **Purpose**: User-facing license information

## 🏢 Commercial Use Guidance

### ✅ What You Can Do
- **Sell OpsConductor** as a commercial product
- **Offer OpsConductor as SaaS** without source disclosure
- **Integrate into proprietary systems** without restrictions
- **Modify and customize** for commercial purposes
- **Create derivative works** under any license

### 📋 What You Must Do
- **Include MIT license notice** in distributions
- **Include NOTICE file** with third-party attributions
- **Maintain copyright notices** for third-party components

### ❌ What You Cannot Do
- **Remove license notices** from distributed copies
- **Claim warranty** - software is provided "as is"
- **Hold contributors liable** for damages

## 🔒 Enterprise Deployment Considerations

### Internal Use
- ✅ **No additional requirements** for internal enterprise use
- ✅ **Can modify freely** without disclosure
- ✅ **Can integrate with proprietary systems**

### Distribution to Customers
- 📋 **Include LICENSE file** in distributions
- 📋 **Include NOTICE file** with third-party attributions
- 📋 **Maintain copyright notices**

### SaaS Deployment
- ✅ **No source disclosure required** for SaaS offerings
- ✅ **Can use proprietary modifications**
- 📋 **Include license information** in user-accessible documentation

## 🛡️ License Compatibility Matrix

| Your License | Third-Party License | Compatible | Notes |
|--------------|-------------------|------------|-------|
| MIT | MIT | ✅ Yes | Perfect compatibility |
| MIT | BSD | ✅ Yes | Permissive, no conflicts |
| MIT | Apache 2.0 | ✅ Yes | Compatible, include notices |
| MIT | LGPL v2.1 | ✅ Yes | Can link, include notices |
| MIT | GPL | ❌ No | Would require GPL for derivative |

## 📝 Compliance Checklist

### ✅ Current Status
- [x] MIT License file created
- [x] NOTICE file with third-party attributions
- [x] README updated with license information
- [x] All dependencies analyzed for compatibility
- [x] LGPL compliance addressed (Paramiko)

### 🔄 Ongoing Requirements
- [ ] **Update NOTICE file** when adding new dependencies
- [ ] **Review licenses** of new third-party components
- [ ] **Include license files** in all distributions
- [ ] **Maintain attribution** for third-party components

## 🚨 Red Flags to Avoid

### ❌ Incompatible Licenses
- **GPL v2/v3** - Would require entire project to be GPL
- **AGPL** - Would require source disclosure for SaaS
- **Proprietary/Commercial** - May have usage restrictions

### ⚠️ License Changes
- **Monitor dependency updates** for license changes
- **Review new dependencies** before adding
- **Update NOTICE file** when licenses change

## 📞 Legal Disclaimer

This guide provides general information about software licensing but is not legal advice. For specific legal questions or complex licensing scenarios, consult with a qualified attorney specializing in intellectual property law.

## 🔄 Updates

This licensing guide should be reviewed and updated:
- When adding new third-party dependencies
- When changing the primary license
- When planning commercial distribution
- Annually as part of compliance review

---

**Last Updated**: January 2024  
**Next Review**: January 2025