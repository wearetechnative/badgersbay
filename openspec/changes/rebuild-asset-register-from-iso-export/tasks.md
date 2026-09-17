# Tasks

## 1. Build the register

- [x] 1.1 Write the thirteen rows below, with the issue dates from the ISO tool
      as both `owner_since` and `valid_from`
- [x] 1.2 Drop the two-row `TARI-00037` construction; Pankhuri Prakash keeps
      `PF3NFHJL` and never swapped
- [x] 1.3 `TARI-00031` carries `YD063JGA`, not `AC06CMEP`
- [x] 1.4 Update `assets.csv.example` to match the shape, with invented names
      and serials - it is committed to a public repository

| asset_id | serial | owner | class | owner_since |
|---|---|---|---|---|
| TARI-00001 | PF2RFH1Z | Pim Snel | linux | 2026-08-14 |
| TARI-00017 | FVFFP1TPQ05N | Sammy Kooti | macos | 2025-05-28 |
| TARI-00022 | PF50L2ML | Mathijs van Veluw | linux | 2024-07-01 |
| TARI-00023 | PF50L2MR | Wouter van der Toorren | linux | 2024-07-01 |
| TARI-00029 | 5CD2308H0Y | Linda de Ridder | windows | 2025-04-03 |
| TARI-00030 | FVFZR9LXL40Y | Bas Anneveld | macos | 2026-02-20 |
| TARI-00031 | YD063JGA | Elma Aker | windows | 2023-06-12 |
| TARI-00034 | PF-4VBTLB | Richard van Os | windows | 2024-03-01 |
| TARI-00037 | PF3NFHJL | Pankhuri Prakash | linux | 2026-06-03 |
| TARI-00041 | MP1Y69AC | Pim Snel | linux | 2026-08-10 |
| TARI-00042 | 190856402801887 | Pim Snel | linux | 2025-03-17 |
| TARI-00045 | FRANDGCPA5530200H9 | Jeroen Penders | linux | 2025-10-22 |
| TARI-00046 | FRANDGCPA550730052 | Luca Kasper | linux | 2025-03-20 |

The register itself is written to the session scratchpad rather than to the
repository: it pairs employee names with hardware serials, which is the reason
it is delivered as a secret. Verified against the real loader - 13 rows, 13
assets, 13 active; `PF50L2MR`, `YD063JGA` and `MP1Y69AC` each resolve to the
right asset and owner, and `AC06CMEP` resolves to nothing.

For the round 2026-09 (scan window 2026-09-01 to 2026-10-29) the loader puts
all 13 in scope, of which 3 are Windows and therefore manual: a denominator of
10.

## 2. Deliver it

- [ ] 2.1 Encrypt with `ragenx -e` from the directory holding `secrets.nix`
- [ ] 2.2 Verify the round trip: `ragenx -d` must return the input byte for byte
- [ ] 2.3 Deploy compute2 and restart badgersbay - the register is read at
      startup, and a deploy alone does not restart the service
      (`elastinix-p8u9`)

## 3. Verify against a running round

- [ ] 3.1 The service starts; a register it cannot trust is a failed start, not
      a silent skip
- [ ] 3.2 The round view shows ten assets in the denominator and three Windows
      machines as manual
- [ ] 3.3 Wouter's existing submission still matches `TARI-00023` - it is the
      only asset currently scanning, so it is the regression test
- [ ] 3.4 The disappeared-asset report names the four rows the previous register
      held, rather than passing over them

## 4. Raise upstream, do not fix here

- [ ] 4.1 Ask the ISO tool administrator to fill `Asset tag` for every asset in
      the register, so the next rebuild is an export rather than a conversation
      (request already made)
- [ ] 4.2 Correct `AC06CMEP` to `YD063JGA` in the ISO tool
- [ ] 4.3 Confirm `YD063JGA` against the sticker under Elma's laptop - one
      reading by the right method, but one reading (`honeybadger-wbq4`)
- [ ] 4.4 Establish what Richard's machine reports for `PF-4VBTLB` once the
      Windows client can submit (`honeybadger-k80g`)
- [ ] 4.5 Report `PF2RFH1Z` and `MP1Y69AC` as unencrypted - both were issued in
      August and the tool records `Encrypted: No`. This is an ISO finding, not a
      register fault, and it is invisible in the export, which renders that
      column as a hex colour.
