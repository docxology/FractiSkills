# Visualizations {#sec:visualizations}

All thirteen figures are generated deterministically by `figures.py` from the persisted analysis record — no hand-drawn numbers — and are written to `output/figures/` with a registry consumed by the manuscript binder. Every figure is auto-numbered and cross-referenceable; captions are bound tokens carrying the observation's own statistics.

![{{FIGURE_SITE_SECTIONS_CAPTION}}](../output/figures/fig1-site-sections.png){#fig:site-sections width=100%}

![{{FIGURE_DISCOVERY_PROVENANCE_CAPTION}}](../output/figures/fig2-discovery-provenance.png){#fig:discovery-provenance width=100%}

![{{FIGURE_CORPUS_SHARE_CAPTION}}](../output/figures/fig3-corpus-share.png){#fig:corpus-share width=100%}

![{{FIGURE_SKILL_SIZE_DISTRIBUTION_CAPTION}}](../output/figures/fig4-skill-size-distribution.png){#fig:skill-size-distribution width=100%}

![{{FIGURE_SECTION_LINK_GRAPH_CAPTION}}](../output/figures/fig5-section-link-graph.png){#fig:section-link-graph width=88%}

![{{FIGURE_AUGMENTATION_CAPTION}}](../output/figures/fig6-augmentation.png){#fig:augmentation width=88%}

![{{FIGURE_DISCOVERY_FUNNEL_CAPTION}}](../output/figures/fig7-discovery-funnel.png){#fig:discovery-funnel width=88%}

![{{FIGURE_CRAWL_DEPTH_CAPTION}}](../output/figures/fig8-crawl-depth.png){#fig:crawl-depth width=88%}

![{{FIGURE_TOP_INDEGREE_CAPTION}}](../output/figures/fig9-top-indegree.png){#fig:top-indegree width=100%}

![{{FIGURE_AUGMENTATION_EFFECT_CAPTION}}](../output/figures/fig10-augmentation-effect.png){#fig:augmentation-effect width=82%}

![{{FIGURE_WORDS_VS_PAGES_CAPTION}}](../output/figures/fig11-words-vs-pages.png){#fig:words-vs-pages width=88%}

![{{FIGURE_CUMULATIVE_WORDS_CAPTION}}](../output/figures/fig12-cumulative-words.png){#fig:cumulative-words width=92%}

![{{FIGURE_SECTION_ADJACENCY_CAPTION}}](../output/figures/fig13-section-adjacency.png){#fig:section-adjacency width=96%}

## Reading the set

The thirteen figures form one argument in four movements. **Structure** ([@fig:site-sections], [@fig:words-vs-pages], [@fig:corpus-share]): the site's mass concentrates in Interfaces and Whitepaper — the two mass-dense sections visible above the corpus-average line in [@fig:words-vs-pages] — while Ship-Blog contributes breadth over depth. **Provenance** ([@fig:discovery-provenance], [@fig:discovery-funnel], [@fig:crawl-depth]): the sitemap alone explains a small slice of the corpus; the funnel's steep second step and the depth histogram's {{DEPTH_MODE_SHARE}}-at-depth-4 mode are the same fact seen from two sides — the crawl's link-following, not the site's declared index, is where the pages live. **Flow** ([@fig:section-link-graph], [@fig:section-adjacency]): the adjacency matrix's densest off-diagonal cells and the graph's thick edges agree that the site is one cross-linked work, with Ship-Blog quoting Core (122 links) and Core answering back (133) as its strongest reading paths. **Augmentation** ([@fig:augmentation], [@fig:augmentation-effect]): the histogram shows what the declared bindings recovered — right-skewed documents clustering near a ten-thousand-character median — and the effect panel prices that recovery at {{AUGMENT_RATIO}}× the median static body. The size distribution of [@fig:skill-size-distribution] and the hub ranking of [@fig:top-indegree] anchor the middle of the story: a broad, hub-linked corpus rather than a spiky one.