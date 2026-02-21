# Bodhi Companion - Setup Documentation

## OS Decision

**Selected OS: Raspberry Pi OS (64-bit)**

### Rationale
- **User Adoption**: Default OS for 95% of Raspberry Pi users
- **Cross-platform Install Script**: Users can install on existing systems (RPi/Linux/Mac/Windows)
- **Hardware Support**: Best GPIO, camera, and hardware accelerator support
- **Containerization**: Docker-based architecture ensures portability
- **Future-proof**: Container images work across ARM64 devices (Jetson, other SBCs)

### Distribution Strategy
**Install Script Approach** - Universal installation via shell script
- Primary: `curl -fsSL https://get.bodhi.dev | bash` (Linux/Mac/RPi)
- Windows: PowerShell equivalent or WSL2 support
- Detects platform, installs Docker if needed, pulls containers, configures services

## Architecture Overview

### Development & Deployment Strategy
- **Development Environment**: Ubuntu PC (x86_64) - for rapid development and testing
- **Deployment Target**: RPi5 (ARM64) - production deployment for personal use
- **User Deployment**: Cross-platform install script (Linux/Mac/Windows/RPi)
- **Portability**: Docker containers ensure code works across architectures

### Host-Client Separation
- **Host Device**: RPi5 (or other device) runs AI models and core services
- **Client Devices**: Laptops, phones, desktops access over local network
- **Network**: Local-only by default, no cloud dependencies
- **Data Locality**: All models and data remain on host device

## Security Architecture

### Principle of Least Privilege
**User-Configurable Access Control**
- Users specify which capabilities the AI can access during setup
- Granular permissions (filesystem, camera, microphone, sensors, network)
- Permission model similar to Android/iOS app permissions
- Revocable at runtime without restart

Example permission scopes:
```yaml
permissions:
  filesystem:
    - read: ["/home/user/documents"]
    - write: ["/home/user/ai-workspace"]
  hardware:
    - camera: false
    - microphone: true
    - gpio: [4, 17, 27]  # specific pins only
  network:
    - local_only: true
    - internet_access: false
```

### Initial Setup Security
- [ ] Firewall configuration (UFW) - only expose on local network
- [ ] API authentication tokens per client device (JWT-based)
- [ ] Container sandboxing with restricted capabilities
- [ ] Automatic security updates for containers
- [ ] SSH key-only authentication (disable password auth)
- [ ] Fail2ban for brute-force protection
- [ ] TLS/SSL for all API endpoints (self-signed + local CA)

### Runtime Security
- [ ] Read-only container filesystems where possible
- [ ] Non-root user inside containers (UID mapping)
- [ ] Network isolation between services (Docker networks)
- [ ] Secrets management (Docker secrets or encrypted env files)
- [ ] Rate limiting per client device
- [ ] Input validation and sanitization
- [ ] SELinux/AppArmor profiles for containers

### Data Privacy & Locality
- [ ] All AI inference happens locally (no cloud calls)
- [ ] User data never leaves local network
- [ ] Encrypted storage for sensitive data (LUKS/eCryptfs)
- [ ] Audit logs for data access (who accessed what, when)
- [ ] Optional: client-side encryption for data at rest
- [ ] Clear data retention policies (user-configurable)

### Network Security (Local Network)
- [ ] mDNS/Avahi for local discovery (bodhi.local)
- [ ] mTLS for client-host communication
- [ ] IP whitelisting (only trusted local devices)
- [ ] VLAN isolation option for paranoid users
- [ ] No UPnP/port forwarding by default

### Remote Access Security (Off-Premise)
**Zero-Trust Network Architecture**

**VPN Options (mutually exclusive):**
1. **Tailscale (Recommended)** - WireGuard-based mesh VPN
   - [ ] Automatic NAT traversal (works behind CGNAT)
   - [ ] MagicDNS for device naming
   - [ ] ACLs for fine-grained access control
   - [ ] Supports all platforms (iOS, Android, Linux, Mac, Windows)
   - [ ] No port forwarding required
   
2. **Self-hosted WireGuard**
   - [ ] Full control, no third-party dependencies
   - [ ] Requires dynamic DNS + port forwarding (or VPS relay)
   - [ ] Manual key management
   - [ ] Lighter weight than Tailscale

3. **Cloudflare Tunnel** (Zero Trust)
   - [ ] No inbound ports opened on home network
   - [ ] Built-in DDoS protection
   - [ ] Web-based access (no VPN client needed)
   - [ ] Cloudflare sees metadata (but not E2E encrypted payload)

**Additional Remote Security Layers:**
- [ ] **Device Attestation** - Only approved devices can connect
  - Hardware-backed keys (TPM, Secure Enclave)
  - Device fingerprinting
  - Certificate pinning
  
- [ ] **Geo-fencing** (optional) - Restrict access by location
  - Alert if access from unusual country
  - Auto-lockdown on suspicious locations
  
- [ ] **Time-based Access Control**
  - Restrict off-premise access to certain hours
  - Emergency "always-on" override
  
- [ ] **Rate Limiting (Aggressive)**
  - Per-device request limits
  - Exponential backoff on auth failures
  - Temporary lockout after 5 failed attempts
  
- [ ] **Connection Monitoring**
  - Real-time alerts for new connections
  - Dashboard showing active sessions
  - Remote kill-switch to disconnect all clients
  
- [ ] **End-to-End Encryption**
  - TLS 1.3 minimum for transport
  - Application-layer encryption (double encryption)
  - Forward secrecy (rotate keys per session)
  
- [ ] **Fallback & Resilience**
  - Offline mode for client (cached responses)
  - Graceful degradation when host unreachable
  - Keep-alive for connection health checks

**Threat Mitigation Strategies:**

| Threat | Mitigation |
|--------|-----------|
| Man-in-the-Middle | mTLS + certificate pinning + VPN encryption |
| Brute Force | Rate limiting + fail2ban + hardware 2FA |
| DDoS | Cloudflare proxy (if using tunnels) or rate limiting |
| Stolen Device | Device attestation + remote wipe capability |
| Compromised Network | VPN-only access + no direct internet exposure |
| Zero-Day Exploits | Auto-updates + minimal attack surface + WAF |
| Insider Threat | Audit logs + permission revocation + principle of least privilege |
| Physical Access to RPi | Full disk encryption (LUKS) + secure boot |

**Remote Access Modes:**

1. **Paranoid Mode** (Maximum Security)
   - VPN required (Tailscale + Cloudflare Tunnel double-layer)
   - Hardware 2FA (YubiKey) for VPN auth
   - Geo-fencing enabled
   - All requests logged and monitored
   - 2-hour session timeout
   
2. **Balanced Mode** (Default)
   - VPN required (Tailscale)
   - TOTP 2FA for initial device pairing
   - Rate limiting enabled
   - 24-hour session timeout
   
3. **Convenience Mode** (Lower Security)
   - Cloudflare Tunnel with password + TOTP
   - Longer session timeouts
   - Less aggressive rate limiting
   - For trusted environments only

### Permission Management
- [ ] Web UI for permission management
- [ ] Runtime permission requests (user must approve first time)
- [ ] Audit trail of permission usage
- [ ] Capability-based security (capabilities dropped in containers)
- [ ] Seccomp profiles to restrict syscalls
- [ ] Read-only bind mounts for sensitive directories

### Optional Advanced Security
- [ ] Hardware security module (TPM 2.0) support
- [ ] Secure boot verification
- [ ] Encrypted swap
- [ ] Memory isolation (cgroups v2)
- [ ] Intrusion detection (OSSEC/Wazuh)
- [ ] Honeypot services for threat detection

## Installation Prerequisites

### Raspberry Pi 5
- Raspberry Pi OS 64-bit (Bookworm or later)
- 4GB+ RAM recommended (8GB for larger models)
- 32GB+ microSD card or NVMe SSD (SSD strongly recommended)
- Active cooling recommended for continuous AI workloads
- Static IP or reserved DHCP lease recommended

## RPi OS Installation (via Raspberry Pi Imager)

### Step 1: Configure in RPi Imager
1. Select **"Raspberry Pi OS (64-bit)"** from OS menu
2. Click **⚙️ Settings (gear icon)** to customize:

**General Settings:**
- Set hostname: `bodhi-host` (or your preference)
- Enable SSH: **✅ Use public-key authentication only**
  - Paste your public key (from `~/.ssh/id_rsa.pub` or `~/.ssh/id_ed25519.pub`)
  - If you don't have one, generate: `ssh-keygen -t ed25519 -C "your_email@example.com"`
- Set username and password (for sudo only, NOT for SSH)
- Configure WiFi (or use Ethernet)
- Set locale settings (timezone, keyboard layout)

**Services:**
- ✅ Enable SSH
- Authentication: **Public-key authentication only** (no password)

**Why public-key only?**
- Immune to brute-force attacks
- No password to leak/forget
- Can be revoked without changing passwords
- Standard practice for servers

### Step 2: First Boot Security Hardening
After flashing and first boot, SSH in and run:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential security tools
sudo apt install -y ufw fail2ban unattended-upgrades

# Configure firewall (UFW)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 192.168.1.0/24 to any port 22  # SSH only from local network
sudo ufw enable

# Verify SSH config (password auth should be disabled)
sudo grep -E '^(PasswordAuthentication|PubkeyAuthentication|PermitRootLogin)' /etc/ssh/sshd_config
# Should show:
# PasswordAuthentication no
# PubkeyAuthentication yes
# PermitRootLogin no

# Enable automatic security updates
sudo dpkg-reconfigure -plow unattended-upgrades

# Reboot to apply changes
sudo reboot
```

### Step 3: Static IP Configuration (Recommended)
Option A: Configure on router (preferred - reserve DHCP lease)
Option B: Configure on RPi:

```bash
# Edit dhcpcd config
sudo nano /etc/dhcpcd.conf

# Add at the end:
interface eth0  # or wlan0 for WiFi
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 1.1.1.1

# Restart networking
sudo systemctl restart dhcpcd
```

### Other Platforms (Future)
- Linux: Ubuntu 22.04+, Debian 12+, Fedora 38+ (ARM64/x86_64)
- macOS: 12+ with Docker Desktop (x86_64/ARM64)
- Windows: Windows 10/11 with WSL2 and Docker Desktop

## Installation Flow

1. **Initial Setup** (on host device)
   - Run install script, detects platform
   - User configures permissions during install
   - Generates client access tokens
   - Sets up firewall rules
   - Starts core services

2. **Client Setup** (on user devices)
   - Scan QR code or enter token manually
   - Auto-discovers host on local network (mDNS)
   - Establishes secure connection (mTLS)
   - Client can now interact with AI

3. **Permission Requests** (runtime)
   - AI requests new permission (e.g., "access camera")
   - User gets notification on client device
   - User approves/denies
   - Permission cached for future use

## Architecture Decisions

### Permission Model
**Whitelist (Deny by Default)**
- AI has no permissions initially
- Must request permissions at runtime
- User explicitly grants access to filesystem, hardware, network
- Revocable without restart

### Multi-Agent Brain Architecture
**Inspired by Human Brain Structure**

**Agent Hierarchy:**
1. **Central Reasoning Agent** - Orchestrates all sub-agents, makes decisions
2. **Sub-Agents** - Specialized agents for different cognitive functions:
   - Perception (vision, audio, sensors)
   - Language processing (NLP, conversation)
   - Motor control (hardware interaction, GPIO)
   - Memory management (retrieval, consolidation)
   - Emotional/context awareness
3. **Evaluation Agent** - Continuously monitors and improves system performance

**Memory System (Three-Tier):**
| Memory Type | Database | Purpose | Retention |
|-------------|----------|---------|-----------|
| **Fast Memory** (Working) | Redis | Active context, current conversation, immediate state | Seconds to minutes |
| **Short-term Memory** | Vector DB (e.g., Qdrant, Milvus) | Recent interactions, semantic search, RAG | Hours to days |
| **Long-term Memory** | PostgreSQL | User preferences, learned behaviors, historical data | Permanent |

**Data Flow:**
1. New information → Redis (working memory)
2. Important context → Vector DB (episodic memory, embeddings)
3. Consolidated knowledge → PostgreSQL (semantic memory, structured data)

**Memory Consolidation:**
- Background process moves data between tiers
- Evaluation agent determines what to keep/forget
- Mimics human memory consolidation during "sleep" cycles

## Next Steps
1. Make architecture decisions (remote access, permissions, storage)
2. Design system architecture diagram
3. Create modular install script with platform detection
4. Set up Docker Compose with security-hardened containers
5. Implement client authentication and token management
6. Build web UI for permission management
7. Set up VPN (Tailscale or WireGuard)
8. Test on RPi5 with fresh OS install
9. Create client SDKs (Python, JavaScript)
10. Write security audit checklist
