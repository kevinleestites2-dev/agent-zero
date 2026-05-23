---
name: pantheon-tools
description: Layer 17 — The Pantheon Tool Belt. Agent Zero can wield any Prime as a native tool call. GhostPrime, ZeusPrime, ScoutPrime, MidasPrime, TerraPrime, FluxPrime, AeonPrime — all callable by Agent Zero as atomic actions. This is the bridge between the Mind and the Machine.
version: 1.0.0
category: orchestration
tags:
  - layer-17
  - pantheon
  - tool-belt
  - orchestration
  - primes
---

# Pantheon Tool Belt — Layer 17

Agent Zero wields the Pantheon.

Every Prime is a tool. Every tool is a weapon. The Mind pulls the trigger.

## Available Tools

| Tool | Prime | Action |
|---|---|---|
| ghost_run | GhostPrime | Fire a stealth traffic swarm cycle |
| ghost_status | GhostPrime | Get swarm health + cycle stats |
| zeus_buy | ZeusPrime | Execute a buy order on-chain |
| zeus_status | ZeusPrime | Get wallet cluster status |
| scout_scan | ScoutPrime | Scan a target (auction, property, URL) |
| scout_bid | ScoutPrime | Register a bid on a scanned target |
| midas_balance | MidasPrime | Get War Chest balance + countdowns |
| midas_sync | MidasPrime | Trigger a metabolic sync cycle |
| terra_task | TerraPrime | Queue a task into TerraPrime's engine |
| terra_status | TerraPrime | Get TerraPrime task queue status |
| flux_cycle | FluxPrime | Trigger a FluxPrime autonomous cycle |
| flux_status | FluxPrime | Get FluxPrime mission + cycle state |
| aeon_signal | AeonPrime | Inject a signal into AeonPrime's vortex |
| nexus_relay | NexusRelay | Send a command to the Red Magic phone |
| nexus_status | NexusRelay | Check Red Magic / NexusClaw status |
| genome_replicate | Genome | Spawn a new Agent Zero replica |
| genome_status | Genome | Get node registry + replication count |
| ethics_check | EthicsCore | Check an action before execution |

## Governor Integration
Every tool call passes through Layer 14 (Governor) and Layer 16 (Ethics Core)
before execution. No Prime can be triggered without clearing both.

## Usage
Agent Zero calls tools autonomously during Prime Cycle (Layer 12).
Forgemaster can also invoke any tool directly via Telegram command.
