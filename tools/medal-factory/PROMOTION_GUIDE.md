# How to Increase Visibility for Your Kaggle Notebooks

After listing and making your notebooks public with `kaggle_promote.py`, use these tactics so more people find, use, and interact with them (views, upvotes, comments, forks).

---

## 1. Optimize the notebook itself

- **Title and subtitle**  
  Use a clear, search-friendly title and a one-line subtitle that states the result or method (e.g. “EDA + XGBoost, LB 0.82”).

- **Description**  
  In the kernel description, add 2–3 short paragraphs: what you did, what the reader will learn, and how to run/adapt it. Include keywords (competition name, task type, methods).

- **Tags**  
  Add all relevant tags (competition, dataset, technique, language) so your notebook appears in filters and search.

- **First cell / intro**  
  Start with a brief intro: goal, dataset, and structure (sections). Makes the notebook easier to skim and more likely to be upvoted.

- **Clean structure**  
  Use markdown headers and short code cells. Clear structure gets more engagement than one long script.

---

## 2. Share on social and community channels

- **Twitter / X**  
  Post when you publish or get a medal. Include: one-line hook, link to notebook, competition/dataset name, and 2–3 hashtags (e.g. `#Kaggle`, `#DataScience`, `#MachineLearning`, competition hashtag if it exists).

- **LinkedIn**  
  Share a short post: what problem you tackled, what approach you used, link to the notebook, and what you learned. Good for visibility to recruiters and other practitioners.

- **Reddit**  
  In subreddits like r/MachineLearning, r/datascience, r/kaggle (if allowed by rules), share the notebook with context: “I built this for [competition X]; it does [Y]. Link: …”. Avoid sounding like an ad; focus on the content.

- **Kaggle Discussions**  
  In the competition or dataset forum, post a short message: “I shared a notebook that does [X]. Feedback welcome: [link].” Stay helpful and on-topic.

---

## 3. Engage on Kaggle

- **Comment on others’ notebooks**  
  Thoughtful comments (questions, suggestions, thanks) often lead to reciprocal visits and upvotes. Don’t ask for upvotes; focus on the code/idea.

- **Answer questions in Discussions**  
  When someone asks something your notebook addresses, reply and mention: “I covered this in my notebook: [link].” That drives targeted traffic.

- **Fork and extend**  
  Fork a popular notebook, add a clear improvement (e.g. better feature, clearer viz), and in the description credit the original and state what you added. Many users discover notebooks via “Fork” and “Related”.

---

## 4. Timing and discoverability

- **Publish early in a competition**  
  Early notebooks get more views and forks. Update with new versions (e.g. “v2 – added feature X”) to keep it relevant.

- **Dataset notebooks**  
  For dataset kernels, publish when the dataset is new or trending. Good titles and tags help it show up in “Notebooks” on the dataset page.

- **Search-friendly wording**  
  Use the exact competition/dataset name and common method names (e.g. “LightGBM”, “EDA”) in title, subtitle, and description so your notebook appears in search.

---

## 5. Use the report from this tool

- Run:  
  `python kaggle_promote.py --list --out my_notebooks.md`  
  You get a markdown file with a table of all your notebooks and their links.

- Use `my_notebooks.md` to:  
  - Paste links into social posts or your portfolio.  
  - Track which notebooks you’ve already promoted.  
  - Build a simple “My Kaggle work” page (e.g. in a GitHub README or personal site) that links to each notebook.

---

## 6. Portfolio and long-term visibility

- **GitHub**  
  Add a “Kaggle” section to your README or a dedicated `kaggle.md` with titles and links (and short descriptions). People searching for your profile will find your work.

- **Personal site / blog**  
  Write a short post per notebook (or per competition): problem, approach, link to kernel, and main takeaway. Link back to your Kaggle profile.

- **Resume / CV**  
  List 2–3 best notebooks with links and one-line descriptions. “Kaggle Notebooks” or “Data science portfolio” works well.

---

## Quick checklist per notebook

- [ ] Public (use `kaggle_promote.py --make-public` if needed)
- [ ] Clear title and subtitle
- [ ] Description and tags filled
- [ ] Intro and structure in the first cells
- [ ] Shared once on Twitter/LinkedIn/Reddit (where appropriate)
- [ ] Mentioned in Kaggle Discussions if it fits a thread
- [ ] Link added to your portfolio/README/GitHub

Consistency beats one-off pushes: a few minutes per notebook (description, tags, one share) usually does more than a single big promotion round.
