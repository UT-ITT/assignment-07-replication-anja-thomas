# Assignment 7 — Replicating Interaction Techniques

**Replicated technique:** The Bubble Cursor

**Team:** Anja & Thomas

---

## 1. Paper Selection

### Candidates considered

Grossman, T., & Balakrishnan, R. (2005). The Bubble Cursor: Enhancing Target Acquisition by Dynamic Resizing of the Cursor's Activation Area. In Proceedings of the SIGCHI Conference on Human Factors in Computing Systems (CHI '05) (pp. 281–290). ACM.

Schmid, M., Fischer, A., Weichart, D., Hartmann, B., & Wimmer, R. (2021). ScreenshotMatcher: Taking Smartphone Photos to Capture Screenshots. In Mensch und Computer 2021. ACM.

ScreenshotMatcher lets a user photograph a PC screen with a smartphone camera; a
desktop companion app matches the photo against a live screenshot via ORB keypoint
detection and feature matching, then crops and returns a high-fidelity,
distortion-free screenshot to the phone over the local WiFi network. We found this an
interesting candidate because it replaces an existing awkward workaround
(photographing a screen and living with distortion) with a
clean interaction technique, and the paper is explicit about its algorithmic pipeline which would have
made it implementable without needing our own training data. We did not end up
picking it because another team already took it, not
because of any scope or feasibility concern with the paper itself.
Given the choice, we felt the bubble cursor was at least as strong a fit for the two-week scope, since
it needs no cross-device networking layer (WiFi discovery, HTTP transfer, Android
app) and no computer-vision pipeline, only mouse input and 2D geometry, which let us
focus more implementation time on the interaction logic itself rather than
infrastructure.
Idea of the bubble cursor: Dynamicly increase cursor size depending on nearest targets. 

### Why we chose the Bubble Cursor

- **Clear, implementable algorithm.** The paper gives a fully specified, closed-form
  rule for the cursor radius at every frame (closest target by intersecting distance,
  second-closest by intersecting distance, radius = `min(ConD_i, IntD_j)`), so the core
  technique can be implemented directly from the paper without guessing at details or
  needing the authors' original code.
- **No hardware or training-data requirements.** Unlike techniques that need eye
  tracking, pen input, or a trained model, the bubble cursor only needs mouse position
  and a set of circular targets, which fits comfortably in a two-week scope. 
  It was important for us to not needany extra hardware.
- **Interesting theory.** Fitts Law was an interesting theoretical basis and we like voronoi diagrams.
- **Scope is appropriately sized.** Implementing the three cursors plus a lightweight
  replication frame for Experiment 1 (1D reciprocal pointing) and Experiment 2
  (2D pointing with distractor density) is substantial but bounded — we deliberately
  did not aim for statistically powered data collection or the full 243-condition
  design, just a working frame that reproduces the main interaction technique, in example the bubble cursor. 
  We layed the framework to repeat the experiment, however we do not have the ressources to repeat them profesionally and
  we wanted to keep the attention on the bubble cursor interaction technique which we think is what u guys had in mind

### Source

Grossman, T. and Balakrishnan, R. (2005). The Bubble Cursor: Enhancing Target
Acquisition by Dynamic Resizing of the Cursor's Activation Area. *ACM CHI Conference
on Human Factors in Computing Systems*, p. 281–290.

Schmid, A., Fischer, T., Weichart, A., Hartmann, A., and Wimmer, R. (2021).
ScreenshotMatcher: Taking Smartphone Photos to Capture Screenshots. *Mensch und
Computer 2021 (MuC '21)*, September 5–8, 2021, Ingolstadt, Germany. ACM.

---

## 2. Implementation Summary


We used simple pyglet for the project as we used that for most of the projects in this lecture. start with python main.py.
We implemented three cursor techniques and a demo/experiment frame around them:

- **Point cursor** — standard single-pixel hotspot, selects whichever target's circle
  contains the cursor position.
- **Bubble cursor** — implements the paper's radius rule every frame: finds the closest
  target by intersecting distance, the second-closest target by intersecting distance,
  and sets the bubble radius to `min(containment distance of closest, intersecting
  distance of second-closest)`. Also implements the "morph" behaviour from Figure 4b,
  where a secondary shape expands from the intersection points to fully envelope the
  captured target when the main bubble only partially overlaps it. This is the Interaction
  technique of the paper we wanted to replicate

- **Object Pointing** — implemented as a secondary, less polished baseline, mainly to
  have a third comparison point as in the paper's Experiment 2.  and the technique the assignment asks us to
  replicate; Object Pointing is a reference baseline, not a focus. Object Pointing was
  already bad in the paper and it was just not attractive for us and so explicitly chose to
  spend most of our implementation effort on the bubble cursor itself, since that is
  the paper's actual contribution and interaction technique we wanted to replicate. So while keeping the scope in mind we thought
  the normal cursor is a perfectly sufficient baseline to compare to.


### Demo mode

`demo_mode.py` reproduces the intuition behind the paper's Figure 1: a scattering of
circular targets of varied sizes, with the current cursor's behaviour visualized live.
Key bindings let a user switch cursor technique and regenerate the target layout:

| Key | Action |
|---|---|
| `1` / `2` / `3` | Switch to Point / Bubble / Object cursor |
| `R` | Generate a new random target layout |
| `T` | Toggle a Voronoi diagram over the target centers |
| `Q` | Return to menu |

### Voronoi overlay

The paper explicitly frames the bubble cursor's effective width in terms of a Voronoi
diagram (Figure 5): the region belonging to each target is the set of points closer to
that target than to any other, and this region is exactly the target's activation
boundary once bubble-cursor selection is applied. We added a toggleable overlay
(`T` key) that draws this diagram over the demo scene using `scipy.spatial.Voronoi`,
with infinite ridges extended far enough that the window edge clips them naturally.
It was important for us to have this since it intuitively explains the bubble cursor for 
the presentation and for you when testing our demo. 
So demo.py showcases the main interaction technique. We put most our effort to make this clean and faithful to
the paper and theoretical basis they had in mind.
### Experiment replication frame
We also replicated the 1D & 2D experiments as stated in the paper. Though we decreased the amount of blocks. You can change that in the code
but i would not recommend that. In the paper the users needed aroud an hour for the test. We needed like 20 minutes. 
It was kind of rough to get through mentally to be honest.
This is why we only made the experiment once for some plots. We think that we lack the scope to replciate the experiment (enough people that have time to do that)
atleast in the stressfull 2 weeks we have right now. I think you also wanted us to have the spotlight on the interaction technique rather than the full paper results.
Our framework works to replicate it though if people would want that. 


## 3. Design Decisions & Challenges

- The simplified version of the Bubble cursor was surprisingly straightforward. We also added the morphing but kept it more simple.
  They did make tiny adjustments which we tried to follow but we did not have their code so it was mostly guesswork from their description.
  The main benefit of the cursor, implementing a dynamically increasing cursor size is definitely faithful to the paper.

- voronoi diagramm was fun and quick to do with scipy.spatial.Voronoi. Def upgraded the demo.

- Object Poiting was very rough and jittery to implement. First we tried to put a cooldown on the jumping on it but that was hard to optimize and felt like was backwards to its identity. Overall the base implementation works but is still rough to use to be honest. Maybe someone with faith in the object pointer could make a paper about and give it a fair implementation.

- experiment 1 & 2 are faithful to the original except the length. The problem here was less technical and more of not understanding the methods. We dont think the tests are "practical". They are tuned to Fitts law which is rigid per defintion. The strenght of the bubble cursors def doesnt need the set in stone EW/W ratios. However it is understandable from a scientific standpoint since fitts law was the basis.

- after being done with everything i tested the setup on my notebook and i couldnt press start because the window was to large. If u cant finde the green start button please just make the window so small that it fits into ur screen. You can do that in config.py


### Results

- Pretty similiar to the paper we found that the bubble cursor was faster than the normal one. We also made less mistakes. However with our small test size its not really enough to say anything. For personal preference on a desktop for example we think the normal cursor is perfectly fine and speed is not as important, this might be bias since we use the normal cursor in our daily life. Its fascinating how we can optimize any little detail and changing how the mouse works in little ways can have huge consequences.




