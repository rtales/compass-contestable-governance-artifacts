# Governing by Artifacts

- [Reviewed LaTeX PDF](artigo_revisado.pdf): 10 pages.
- [Editable ACM Word document](artigo_acm_corrigido.docx): 12 pages in the checked LibreOffice rendering, with 106 native OMML expressions, 14 native tables and 23 references.
- [LaTeX source](latex/main.tex): the transitive input, bibliography and figure files used by the reviewed manuscript. Compile with the `acmart` class and standard ACM/LaTeX packages, for example `tectonic main.tex` from `latex/`.
- [Recomputed reports and aggregate results](results/).
- [Frozen scientific reproduction package](../reproduction/2026-10-20/README.md).

The PDF and Word are different typesetting outputs of the same reviewed scientific content. The Word preserves editable equations and approximates the ACM two-column layout. The bundled LibreOffice renderer substitutes some mathematical fonts and ignores some OMML size settings; appearance and editing directly in Microsoft Word have not been verified. No ACM TAPS certification is claimed. The archived model used for Word contained older demonstration metadata, which was removed from the article.

The exploratory study has 16 volunteers and eight standardized scenarios. No formal ethics-committee approval or exemption was obtained; this is disclosed in the manuscript. Diagnostic and remediation correctness coincide on the responses, so they are not independent replications. Participant-level responses are not distributed here.

The LaTeX directory is a build copy. To regenerate scientific evidence, use the frozen ZIP, whose original paths are preserved, rather than relocating its analysis scripts. Existing processed snapshots in the application retain their original data terms; the code MIT license does not relicense datasets or third-party templates.
