# 0003. Compliance Rules Behind Ports And Adapters

- Status: Proposed
- Date: 2026-11-10

devnet checks compliance with its own small rule engine. Each system that gives data, and each device driver, is an adapter behind a port. The engine imports no system and no driver. It replaces the engine of the old project (`compliance_pipelines`).

## Why

- Compliance covers more than one system: device config and NetBox data now, other systems later. The old engine takes the config text of one Cisco device
- The device driver can change. pyATS is in use, and scrapli is on the roadmap. With a port, one adapter imports the driver
- The engine is small: scope, run each rule, collect the outcomes. The golden config tools compare a whole intended config. The rules of devnet are single facts
- Rules are data in the config file. A new rule of a known kind needs no code

## Consequences

- Two ports: `Source` (one kind of data about a device) and `DeviceCli` (show commands on a device). See [the plan](../plans/compliance-framework.md#ports-and-adapters)
- A rule asks for its data by class. The engine collects each kind of data one time for each device, and only if a rule asks
- New dependency: `netutils` (Apache-2.0, no dependencies). It has a config parser for each network OS, and one set of OS names with the name that each driver uses. It stays behind `ConfigTree`
- A driver is an optional dependency. Only the environment that uses `PyatsCli` installs pyATS
- Import contracts keep the engine free of systems and drivers

## Alternatives

| Alternative                                                                      | Why not                                                                                                   |
| -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Keep the old engine                                                              | One input (config text). pyATS, Prefect and the parser are imported in each layer                         |
| Golden config: Nautobot Golden Config, `netutils.config.compliance`, hier_config | Compares a whole intended config, so each platform needs a template. Possible later as one more rule kind |
| ciscoconfparse2 as the parser, as in the old project                             | GPL-3.0 license. 13 dependencies, 9 of them with one exact version                                        |
| Batfish                                                                          | One more service to run. It models the whole network, which these checks do not need                      |
| A policy engine (OPA, Rego)                                                      | A second language and one more service. The rules need Python to parse a config                           |
| pyATS and Genie in the rules, without a port                                     | The driver cannot change without a change to each rule and each test                                      |
