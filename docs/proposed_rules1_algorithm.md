# Construction de la feuille `Proposed rules1`

## 1. Résumé exécutif

`Proposed rules1` est une feuille additive, construite après `Proposed rules`, destinée à tester une présentation plus lisible sans casser le contrat historique de `Proposed rules`. Elle consolide des propositions de règles issues de trois familles de flux : `intra-app`, `ingress` et `egress`, selon les stratégies activées en ligne de commande (`allow`, `finegrained`, `blacklist` ou `none`).

La feuille finale contient par défaut les colonnes suivantes :

| Colonne | Signification |
|---|---|
| `Direction` | Famille de flux : `intra-app`, `ingress`, `egress`. |
| `Strategy` | Stratégie demandée : `allow`, `finegrained`, `blacklist`. |
| `Source` | Côté source de la règle proposée. Peut être un rôle, une liste de rôles, un sélecteur de labels ou une IPList. |
| `Destination` | Côté destination de la règle proposée. Même logique que `Source`. |
| `Services` | `All Services`, complément d'une blacklist, ou liste de services `proto/port` séparés par `;`. |
| `num_aggregated_rows` | Nombre de lignes `Flow-Rule Match` agrégées dans la ligne proposée. C'est l'ancien `sum_num_flows` avant normalisation. |
| `sum_num_flows` | Somme réelle des flux, issue de `num_flows_true` quand disponible. |
| `Rule Section` | Emplacement logique/physique de la règle : `Intrascope`, `intra-scope`, `Extrascope`, `Extrascope in other scope`, `Unscopped in OUTBOUND2...`, `North South default rule`, etc. |
| `Comment` | Marque les exceptions et les cas à investiguer : `Blacklist default rule`, `Blacklist Exception`, commentaires de ports, Bouquets, etc. |
| `Ruleset` | Ruleset cible, généralement `<app>-<env>-RS` ou `<app>-<env>-OUTBOUND2<PREFIX>-RS`. |
| `East-West (Y/N)` | Colonne ajoutée seulement si `--network-zone` est activé. Les lignes North/South valent `N`; les autres sont complétées à `Y` par défaut. |

## 2. Pipeline global

| Étape | Condition d'entrée | Traitement | Sortie / effet |
|---|---|---|---|
| 1 | Un chemin Excel est fourni. | La feuille d'analyse principale est écrite, puis la génération des règles proposées démarre. | Début du bloc `Proposed rules` / `Proposed rules1`. |
| 2 | `strategy_intra_app != none`. | Génère d'abord des lignes intra-app historiques pour `Proposed rules`, puis régénère les lignes intra-app pour `Proposed rules1`. Si la stratégie est `blacklist`, les intervalles de blacklist sont obligatoires et lus depuis `carto.conf`. | Lignes intra-app V1 ajoutées à `pr_rows1`. |
| 3 | `strategy_ingress != none`. | Génère les lignes ingress. Pour `Proposed rules1`, les lignes intra-scope héritées sont reprises avec commentaires, puis les lignes `peer_type=labels` Extrascope sont reconstruites par la fonction V1. | Lignes ingress V1 ajoutées à `pr_rows1`. |
| 4 | `strategy_egress != none`. | Génère les lignes egress. Pour `Proposed rules1`, la fonction V1 améliore surtout `finegrained` et `blacklist`; `allow` conserve le comportement historique avec ajout des cas labels V1. | Lignes egress V1 ajoutées à `pr_rows1`. |
| 5 | `--network-zone` activé et zone inverse `ZNOT_<zone>` disponible. | Ajoute des règles North/South par scope : une règle ingress depuis `ZNOT...` vers les rôles du scope et/ou une règle egress depuis les rôles du scope vers `ZNOT...`, selon les stratégies activées. | Lignes `North South default rule` ajoutées au début de `pr_rows1`. |
| 6 | Aucune ligne V1 n'a été produite, mais `Proposed rules` contient des lignes. | Fallback : copie les lignes historiques dans `Proposed rules1` en ajoutant `Comment` et `sum_num_flows_true`. | Garantit l'existence de `Proposed rules1` dans les cas legacy. |
| 7 | Des lignes `Proposed rules1` existent. | Post-traitements : regroupement ingress/finegrained, commentaires de listes de ports, marquage Bouquets, tri, couleurs, normalisation des compteurs, ajout éventuel de `East-West (Y/N)`, écriture Excel. | Feuille finale écrite. |

## 3. Algorithme intra-app

| Stratégie | Sélection | Conditions d'exclusion | Agrégation | Source | Destination | Services | Rule Section | Comment | Compteurs |
|---|---|---|---|---|---|---|---|---|---|
| Toutes | Scope déduit du premier couple `anchor_app` / `anchor_env` non vide. Rôles lus depuis `export_wkld.m.csv`; à défaut, rôles vus dans `anchor_role` et `peer_role`. | Si app/env introuvable : aucune ligne. Si aucun rôle pour `allow` ou `blacklist` : aucune ligne. | Ruleset `<app>-<env>-RS`. | Selon stratégie. | Selon stratégie. | Selon stratégie. | `Intrascope` sauf exceptions blacklist historiques. | Ajusté dans `Proposed rules1`. | `num_flows` et `num_flows_true`. |
| `allow` | Toutes les lignes `direction=intra-app`. | Aucun rôle => rien. | Une seule règle large par scope. | Tous les rôles triés, séparés par `|`. | Même liste que Source. | `All Services`. | `Intrascope`. | Le code met actuellement `Blacklist default rule` sur cette ligne historique, puis `Proposed rules1` ne le retire pas pour `allow`. | Somme de tous les flux intra-app. |
| `finegrained` | Lignes `direction=intra-app`. | Ignore les lignes sans rôles source/destination ou sans services. | Groupe par `(src_role, dst_role)` et agrège les services. Exception : les ports configurés comme ports à garder seuls ne sont pas agrégés et restent par `(src_role, dst_role, service)`. | `src_role`. | `dst_role`. | Services observés triés et séparés par `;`, ou un seul port si port isolé. | `Intrascope`. | Vide. | Somme par groupe, avec somme réelle via `num_flows_true`. |
| `blacklist` sans intervalles | Cas défensif : se comporte comme `allow`, stratégie conservée à `blacklist`. | Aucun rôle => rien. | Une règle large. | Tous les rôles. | Tous les rôles. | `All Services`. | `Intrascope`. | Dans `Proposed rules1`, devient `Blacklist default rule`. | Somme de tous les flux intra-app. |
| `blacklist` avec intervalles | Lignes `direction=intra-app`. | Ignore les lignes sans rôles ou sans ports valides pour exceptions. | 1 règle par défaut + exceptions par `(src_role, dst_role)` pour ports blacklistés observés. | Défaut : tous les rôles. Exceptions : `src_role`. | Défaut : tous les rôles. Exceptions : `dst_role`. | Défaut : complément TCP/UDP de la blacklist + ICMP/IGMP. Exceptions : ports blacklistés observés. | Défaut : `Intrascope`; exceptions initialement `Intrascope Exceptions`, puis réécrites en `Intrascope` dans `Proposed rules1`. | Défaut : `Blacklist default rule`; exceptions : `Blacklist Exception`. | Défaut = flux non blacklistés; exceptions = flux blacklistés par paire. |

## 4. Algorithme ingress

### 4.1 Ingress avec `peer_type=iplist`

| Stratégie | Sélection | Conditions d'exclusion | Agrégation | Source | Destination | Services | Rule Section | Comment dans `Proposed rules1` |
|---|---|---|---|---|---|---|---|---|
| Toutes | `direction=ingress`, `Info != Bouquets Infra`, `peer_type=iplist`. | App/env/rôle/proto/port/IPList manquant, port non positif, préfixe IPList vide. | Les IPLists sont séparées par préfixe significatif : on ne groupe jamais des IPLists de préfixes différents. | IPLists selon stratégie. | Rôles selon stratégie. | Selon stratégie. | `intra-scope`. | Selon stratégie. |
| `allow` | IPLists ingress valides. | Aucun groupe => aucune ligne. | Une règle par `(scope, préfixe IPList)`. | Toutes les IPLists du préfixe, triées et séparées par `|`. | Tous les rôles du scope, triés et séparés par `|`. | `All Services`. | `intra-scope`. | Vide. |
| `finegrained` | IPLists ingress valides. | Idem. | Groupe par `(app, env, role, iplist_prefix, proto, port)`. | IPLists du groupe. | Rôle ciblé. | Un token `proto/port`. | `intra-scope`. | Vide. Après coup, `Proposed rules1` peut regrouper plusieurs services par même Source/Destination. |
| `blacklist` sans intervalles | Cas défensif. | Aucun rôle => rien. | Une règle par scope. | `Any (0.0.0.0/0)`. | Tous les rôles du scope. | `All Services`. | `intra-scope`. | `Blacklist default rule`. |
| `blacklist` avec intervalles | IPLists ingress valides. | Idem. | 1 règle par défaut par scope + exceptions par `(role, préfixe, proto, port)` uniquement pour ports blacklistés observés. | Défaut : `Any (0.0.0.0/0)`. Exceptions : IPLists du groupe. | Défaut : tous les rôles. Exceptions : rôle ciblé. | Défaut : complément blacklist. Exceptions : port blacklisté. | `intra-scope`. | Défaut : `Blacklist default rule`; exceptions détectées dans V1 car Source != `Any`, donc `Blacklist Exception`. |

### 4.2 Ingress avec `peer_type=labels` / Extrascope

| Stratégie | Sélection | Conditions d'exclusion | Agrégation | Source | Destination | Services | Rule Section | Comment |
|---|---|---|---|---|---|---|---|---|
| Toutes | `direction=ingress`, `peer_type=labels`, `matched_rule_category != Bouquets Infra rule`. | App/env/rôle d'ancrage manquant, proto absent, port absent ou non positif, selector source impossible à construire. Les trafics proto-only type ICMP/IGMP ne sont pas traités ici. | Fonction V1 dédiée. | Sélecteur dérivé de `peer_value`. | `anchor_role`. | Selon stratégie. | `Extrascope`. | Selon stratégie. |
| `allow` | Labels ingress valides. | Idem. | Groupe par `(anchor_app, anchor_env, anchor_role, source_selector)`. | Source selector. | Anchor role. | Les services observés sont agrégés; il n'y a pas de conversion en `All Services` dans la V1 labels ingress. | `Extrascope`. | Vide. |
| `finegrained` | Labels ingress valides. | Idem. | Même groupe que `allow`; services observés agrégés. | Source selector. | Anchor role. | Services triés `;`. | `Extrascope`. | Vide. Puis regroupement global possible par Source/Destination. |
| `blacklist` | Labels ingress valides. | Idem. | Non-blacklistés : groupe par `(anchor_app, anchor_env, anchor_role, source_selector)`. Blacklistés : groupe séparé par `(anchor_app, anchor_env, anchor_role, source_selector, proto, port)`. | Source selector. | Anchor role. | Non-blacklistés agrégés; blacklistés un port par ligne. | `Extrascope`. | Blacklistés : `Blacklist Exception`; autres : vide. |

## 5. Algorithme egress

### 5.1 Egress avec `peer_type=iplist`

| Stratégie | Sélection | Conditions d'exclusion | Agrégation | Source | Destination | Services | Rule Section | Comment |
|---|---|---|---|---|---|---|---|---|
| Toutes | `direction=egress`, `Info != Bouquets Infra`, `peer_type=iplist`. | App/env/rôle/proto/port/IPList manquant, port non positif. `peer_value` multi-valeur est éclaté par `|` ou retour ligne pour garantir une seule IPList par ligne destination. | Ruleset `<app>-<env>-RS`, section `intra-scope`. | Rôles agrégés. | Une IPList. | Selon stratégie. | `intra-scope`. | Selon stratégie. |
| `allow` | Comportement historique, puis ajout des labels V1. | Selon fonction historique. | La V1 n'améliore pas l'agrégation IPList pour `allow`. | Historique. | Historique. | `All Services` en logique historique. | Historique. | Vide sauf cas historiques. |
| `finegrained` | IPLists egress valides. | Idem. | Destination-centric : groupe par `(app, env, ruleset, section, IPList)`, sauf ports configurés à garder seuls qui ajoutent le service dans la clé. | Tous les rôles source triés, séparés par `;`. | IPList unique. | Tous les services observés triés `;`, ou un seul service pour ports isolés. | `intra-scope`. | Vide. |
| `blacklist` sans intervalles | Règle par défaut par scope. | Aucun rôle => rien. | Défaut seulement; non-blacklisté couvert par `All Services`. | Tous les rôles du scope séparés par `;`. | `Any (0.0.0.0/0)`. | `All Services`. | `intra-scope`. | `Blacklist default rule`. |
| `blacklist` avec intervalles | Tous les flux egress non Bouquets pour le défaut; IPLists egress pour exceptions. | Idem. | Défaut par scope + exceptions uniquement pour ports blacklistés observés, groupées par `(app, env, ruleset, section, IPList, proto, port)`. Les ports non blacklistés ne produisent pas de ligne IPList car couverts par le défaut. | Défaut : tous les rôles du scope. Exceptions : rôles ayant observé le port vers l'IPList. | Défaut : `Any (0.0.0.0/0)`. Exceptions : IPList unique. | Défaut : complément blacklist. Exceptions : port blacklisté. | `intra-scope`. | Défaut : `Blacklist default rule`; exceptions : `Blacklist Exception`. |

### 5.2 Egress avec `peer_type=labels`

| Stratégie | Sélection | Conditions d'exclusion | Cas de placement | Source | Destination | Services | Rule Section | Ruleset | Comment |
|---|---|---|---|---|---|---|---|---|---|
| Toutes | `direction=egress`, `peer_type=labels`, `matched_rule_category != Bouquets Infra rule`. | App/env/rôle anchor manquant; proto absent; port non positif; `peer_value` sans `app`/`env`/préfixe. Les trafics proto-only ne sont pas traités. En `network-zone`, les flux North/South labels ne sont gardés que si `Info == No Match`. | Parse le `peer_value` en `peer_app`, `peer_env`, `peer_role`, préfixe, et statut managed. | Sélecteur anchor `app=<anchor_app>|env=<anchor_env>|role=<roles>`. | Selon statut managed. | Selon stratégie. | Selon statut managed. | Selon statut managed. | Selon stratégie. |
| Destination managed | Même sélection. | Idem. | Si le préfixe applicatif destination est managed. | Anchor app/env + rôles agrégés. | `app=<peer_app>|env=<peer_env>|role=<peer_role ou All Roles>`. | Selon stratégie. | `Extrascope in other scope`. | `<peer_app>-<peer_env>-RS`. | Selon stratégie. |
| Destination unmanaged | Même sélection. | Idem. | Si le préfixe n'est pas managed. | Anchor app/env + rôles agrégés. | `app=<peer_app>|env=<peer_env>` sans rôle. | Selon stratégie. | `Unscopped in OUTBOUND2<PREFIX>`. | `<anchor_app>-<anchor_env>-OUTBOUND2<PREFIX>-RS`. | Selon stratégie. |
| `allow` | Labels egress valides. | Idem. | Groupe par `(ruleset, section, anchor_app, anchor_env, destination)`. | Rôles anchor agrégés. | Destination managed/unmanaged. | `All Services`. | Placement calculé. | Placement calculé. | Vide. |
| `finegrained` | Labels egress valides. | Idem. | Groupe par destination; les ports configurés à garder seuls ajoutent le service dans la clé. | Rôles anchor agrégés. | Destination managed/unmanaged. | Services observés triés `;`, ou port isolé. | Placement calculé. | Placement calculé. | Vide. |
| `blacklist` | Labels egress valides. | Idem. | Ports blacklistés : groupe séparé par `(ruleset, section, anchor_app, anchor_env, destination, proto, port)`. Autres ports : groupe par destination. | Rôles anchor agrégés. | Destination managed/unmanaged. | Exceptions : port blacklisté. Autres : services observés, pas de `All Services` automatique dans ce bloc labels. | Placement calculé. | Placement calculé. | Exceptions : `Blacklist Exception`; autres : vide. |

## 6. Règles North/South avec `--network-zone`

| Condition | Règle créée | Source | Destination | Services | Compteurs | Comment / East-West |
|---|---|---|---|---|---|---|
| `network_zone_nets` et `network_zone_znot` actifs, scopes `(anchor_app, anchor_env)` inférés. | Ingress si `strategy_ingress != none`. | `ZNOT_<zone>`. | Tous les rôles du scope depuis `export_wkld.m.csv`, sinon rôles vus, sinon `All Roles`. | `All Services`. | `num_aggregated_rows=1`, `sum_num_flows=0`. | `Rule Section=North South default rule`, `Comment=North South default rule`, `East-West=N`. |
| Même condition. | Egress si `strategy_egress != none`. | Tous les rôles du scope. | `ZNOT_<zone>`. | `All Services`. | `num_aggregated_rows=1`, `sum_num_flows=0`. | Même commentaire, `East-West=N`. |
| Aucun scope inférable. | Aucune ligne North/South. | - | - | - | - | Warning. |

## 7. Post-traitements spécifiques à `Proposed rules1`

| Post-traitement | Condition | Détail |
|---|---|---|
| Regroupement ingress finegrained | Ligne `Direction=ingress`, `Strategy=finegrained`, `Rule Section` dans `{intra-scope, Extrascope}`. | Groupe par `(Direction, Strategy, Source, Destination, Rule Section, Ruleset, Comment)`, concatène les services et additionne les compteurs. Si un service est dans les ports configurés pour rester seuls, la ligne n'est pas regroupée. |
| Commentaires de listes de ports | `port_list_intervals` disponible. | Ajoute au `Comment` les indications liées aux ports présents dans `Services`. |
| Marquage Bouquets | Option `mark_potential_core_service` active. | Charge les apps/IPLists référencées par les rulesets `BOUQUETS_` dans `export_rules.enabled.csv`; si une ligne Proposed rules1 référence ces apps/IPLists, ajoute `Remote (App label/iplist) used in Bouquets`. |
| Tri final | Toujours si lignes présentes. | Priorité : egress marqué Bouquets, ingress marqué Bouquets, autres marqués, egress normal, ingress normal, autres. Puis tri par remote principal, ruleset, section, destination, source, services, comment. |
| Couleur rouge | Ligne détectée par `_pr1_matches_to_investigate`. | Marque les lignes à investiguer. La détection couvre notamment les règles `Unscopped in OUTBOUND2...`, selon la logique dédiée. |
| Couleur orange | Marquage Bouquets actif et commentaire Bouquets présent. | Met en évidence les potentiels core services. |
| Gras | `Comment` contient `Blacklist default rule`. | Toute la ligne est écrite en gras. |
| Normalisation compteurs | Toujours. | `sum_num_flows` temporaire devient `num_aggregated_rows`; `sum_num_flows_true` devient le `sum_num_flows` final. Si `sum_num_flows_true` absent, on réutilise l'ancien `sum_num_flows`. |
| Colonne East-West | `network_zone_nets` actif. | Ajoute la colonne avant `Rule Section`; les lignes sans valeur explicite reçoivent `Y`. |

## 8. Points d'attention à discuter avec l'équipe

| Sujet | Pourquoi c'est important |
|---|---|
| `allow` intra-app conserve un commentaire `Blacklist default rule`. | Cela semble incohérent pour une stratégie `allow` et peut induire l'équipe en erreur. |
| Certains compteurs `sum_num_flows_true` ingress blacklist par défaut semblent initialisés à zéro et non incrémentés. | La colonne finale `sum_num_flows` peut donc être sous-renseignée pour ces lignes. |
| Ingress labels `allow` n'écrit pas `All Services`, mais agrège les ports observés. | Ce comportement est différent de l'intuition habituelle de `allow`. |
| Egress labels `blacklist` produit des lignes non-blacklistées par services observés, en plus des exceptions. | À valider : est-ce souhaité ou faut-il couvrir les non-blacklistés par une règle par défaut comparable aux IPLists ? |
| Les trafics proto-only, ICMP/IGMP observés dans les flux, sont ignorés dans les blocs labels ingress/egress. | À clarifier si ces protocoles doivent produire des règles. |
| Les règles North/South ajoutent `num_aggregated_rows=1` mais `sum_num_flows=0`. | C'est volontaire pour représenter une règle par défaut, mais cela peut perturber les analyses quantitatives. |
| Plusieurs séparateurs coexistent : `|`, `;`, retour ligne. | Source/Destination/Services n'ont pas un format unique selon le cas; cela peut nuire à la consommation automatique. |
