# This file
#   creates visualizations of
#   1) overall mentions of rapporteurs over time
#   2) mentions of all rapporteurs by mention type
#   3) mentions of top 5 rapporteurs over time by mention type
#   4) most frequent nouns in non-AIxxx paragraphs
#   5) rapporteurs' top context term


# (0) Setup----

library(lubridate)
library(plotly)
library(tidyverse)
source("./helpers/theme_rapp_plotting.R") # load custom theme from separate file

dataset_description <- read_file("./helpers/dataset_description.txt")

# (1) Overall mentions of all rapporteurs over time----

# load data
rap.time_gen <- read_csv("./data/output_ready/rapporteur_mentions_overtime.csv") %>%
  # transform to quarterly data
  mutate(date_q = zoo::as.yearqtr(date)) %>% 
  group_by(date_q) %>% 
  summarize(rapp_mentioned = sum(rapp_mentioned)) %>% 
  ungroup()

# plot 
p1_rap_all_overtime <- ggplot(data=rap.time_gen, aes(x=date_q, y=rapp_mentioned)) + 
  geom_line() + 
  labs(title = "Prevalence of rapporteurs over time",
       x="", 
       y ="Overall rapporteur mentions", 
       fill='Mention type',
       caption = dataset_description) +
  scale_x_continuous(limits = c(2015, 2023), n.breaks = 9) +
  coord_cartesian(xlim = c(2015, 2023)) + 
  theme_custom_rapp() +
  theme(axis.text.x=element_text(hjust=-1.05),    
        plot.margin = unit(c(1,2,1,1), "cm"))  # margin(t, r, l, b) 

p1_rap_all_overtime

ggsave(p1_rap_all_overtime, filename = './output/1-all_rapporteurs_over-time.png',
       width = 4000, height=2000, units = 'px')

rm(rap.time_gen, p1_rap_all_overtime)

# (2) Mentions of all rapporteurs by mention type----

# names to print for each rapporteur
rap.printnames <- read_csv("./data/preprocessed/rapporteurs_preprocessed_backup.csv") %>% select(-`...1`, -primary)

# overall mentions of rapporteurs
rap.time_rap_type <- read_csv("./data/output_ready/mentions_qrtr_rapp_type.csv") %>% 
  left_join(., rap.printnames, by=c('rapporteur'='lastname')) %>% 
  select(newsletter_date, printname, mention_type, mentions) %>% 
  rename(rapporteur=printname) %>% 
  filter(mentions>0, # drop unmentioned combinations
         mention_type != 'overall_total')

# determine order of rapporteurs to plot in
if(TRUE){
  rapporteurs_order_AIact <- rap.time_rap_type %>% 
    filter(mention_type=="AIact") %>% 
    select(rapporteur, mentions) %>% 
    group_by(rapporteur) %>% 
    summarise(mentions=sum(mentions)) %>% 
    ungroup() %>% 
    arrange(mentions) %>% 
    pull(rapporteur)
  
  rapporteurs_order_AIgen <- rap.time_rap_type %>% 
    filter(mention_type=="AIgen", 
           !rapporteur %in% rapporteurs_order_AIact) %>% 
    select(rapporteur, mentions) %>% 
    group_by(rapporteur) %>% 
    summarise(mentions=sum(mentions)) %>% 
    ungroup() %>% 
    arrange(mentions) %>% 
    pull(rapporteur)
  
  leftover_rapporteurs_order <- rap.time_rap_type %>% 
    filter(!rapporteur %in% rapporteurs_order_AIact,
           !rapporteur %in% rapporteurs_order_AIgen) %>% 
    select(rapporteur) %>% 
    unique() %>% 
    separate(rapporteur, sep=' ', into=c('firstname', 'lastname'), extra = 'merge') %>% 
    arrange(desc(lastname)) %>% 
    mutate(rapporteur = paste(firstname, lastname)) %>% 
    pull(rapporteur)
  
  rapporteurs_order <- c(leftover_rapporteurs_order, rapporteurs_order_AIgen, rapporteurs_order_AIact)
}

# reorder rapporteurs in rap.time_rap_type
rap.time_rap_type <- rap.time_rap_type %>% 
  mutate(rapporteur = fct_relevel(rapporteur, rapporteurs_order),
         mention_type = fct_relevel(mention_type, 'overall_paragraph', 'AIgen', 'AIact'))

# plot rapporteur mentions by type
p2_rap_all_type <- 
  ggplot(data = rap.time_rap_type %>% 
           group_by(rapporteur, mention_type) %>% 
           summarize(mentions=sum(mentions), .groups = 'keep') %>% 
           ungroup(), aes(y=rapporteur, x=mentions, fill=mention_type)) + 
  geom_bar(position = 'stack', stat="identity") +
  #geom_bar(position = position_dodge2(preserve = "single", padding=0), stat="identity") +
  scale_fill_grey(start=0.8, end=0.2, 
                  labels=c("AIact" = "related to AI act",
                           "AIgen" = "related to AI but not AI act", 
                           "overall_paragraph" = "other"),
                  guide=guide_legend(reverse = TRUE)) + 
  labs(title = "Prevalence of rapporteurs by mention type",
       x ="Number of mentions", 
       y="", 
       fill='Mention type',
       caption = paste0(dataset_description, "\nRapporteurs ordered by number of mentions related to AI act and AI.")) +
  theme_custom_rapp() +
  theme(legend.position = 'bottom')

p2_rap_all_type

ggsave(p2_rap_all_type, filename = './output/2-all_rapporteurs_mention-type.png',
       width = 4000, height=2000, units = 'px')

rm(p2_rap_all_type, leftover_rapporteurs_order, rapporteurs_order_AIact, rapporteurs_order_AIgen)

# (3) Mentions of top 5 rapporteurs over time by mention type----

p3_rap_top5_timetype <-
  rap.time_rap_type %>% 
  filter(rapporteur %in% tail(rapporteurs_order, 5),
         mention_type %in% c("AIact", "AIgen")) %>% 
  mutate(date_q=zoo::as.yearqtr(newsletter_date),
         date_y=zoo::as.yearqtr(newsletter_date) %>% lubridate::year(.),
         mention_type = case_when(mention_type=="AIact" ~ "AI act mentions",
                                  mention_type=="AIgen" ~ "AI mentions (excl. AI act)",
                                  TRUE ~ as.character(mention_type))
         ) %>% 
  
  ggplot(data=., aes(x=date_y, y=mentions, fill=rapporteur)) +
  geom_bar(stat = "identity", position="stack") +
  scale_fill_grey(start=0.8, end=0.2,
                  guide=guide_legend(reverse = TRUE)) +
  ggtitle("Prevalence of top 5 rapporteurs on AI act over time") + 
  xlab("Date") + 
  ylab("Number of AI act-related mentions") +
  labs(fill='Rapporteur', caption = dataset_description)+
  #labs(fill='Type of mention')  + 
  theme_custom_rapp() +
  facet_wrap(~mention_type) 

p3_rap_top5_timetype

ggsave(p3_rap_top5_timetype, filename = './output/3_top5-rapporteurs_time-type.png', width = 4000, height=2000, units = 'px')

rm(rapporteurs_order, p3_rap_top5_timetype, rap.time_rap_type)

# (4) Most frequent terms (nouns) in non-AIxxx paragraphs----
term.top1000 <- read_csv("./data/output_ready/_term_counts_overall.csv") %>% select(-`...1`) %>% 
  arrange(desc(counts)) %>% 
  mutate(term = str_replace_all(term, 'mep', 'MEP'),
         term = fct_reorder(term, counts))

n_terms <- 25

p4_term_topterms_overall <- 
  ggplot(data=term.top1000 %>% head(n_terms), aes(x=counts, y=term)) + 
  geom_bar(stat = "identity", position="stack") +
  labs(title='Most frequent nouns in non-AI paragraphs\nthat mention a rapporteur',
       x='Frequency', y='', 
       caption=paste0("\n", dataset_description)) + 
  theme_custom_rapp()

p4_term_topterms_overall

ggsave(p4_term_topterms_overall, filename = './output/4_terms-topterms-overall.png', width = 4000, height=2000, units = 'px')

rm(p4_term_topterms_overall, term.top1000, n_terms)
  
# (5) rapporteurs' top context term----
term.rap_top1 <- read_csv("./data/output_ready/_top_terms_rapporteurs.csv") %>% select(-`...1`) %>% 
  left_join(., rap.printnames, by=c('rapporteur'='lastname')) %>% 
  select(printname, token, count) %>% 
  rename(rapporteur=printname) %>% 
  mutate(rapporteur_fct=fct_reorder(rapporteur, count)) %>% 
  arrange(desc(count)) %>% 
  separate(rapporteur, sep=' ', into=c('f', 'lastname'), extra='merge') %>% 
  mutate(tooltip = paste0("Rapporteur: ", lastname, "\nTop term: ", token, "\nCount: ", count)) %>% 
  mutate(token = paste0("italic('", token, "')"),
         token = fct_reorder(token, count)) %>% 
  select(rapporteur_fct, count, token, tooltip)

p5_top_rap_terms <- ggplot(data=term.rap_top1, aes(x=count, y=rapporteur_fct, label=token)) + 
  geom_bar(stat = "identity", position="stack", fill='#9A9A9A') +
  geom_text(x=1, hjust=0, nudge_x = 10, color="black", parse=TRUE) + 
  xlim(c(0, term.rap_top1$count %>% max() + 40)) +
  labs(title='Most frequent nouns in non-AI paragraphs mentioning rapporteurs',
       x='Frequency', y='', 
       caption=paste0("\n", dataset_description, " Excluding rapporteur names.")) + 
  theme_custom_rapp()+
    theme(legend.position = 'none')

p5_top_rap_terms

ggsave(p5_top_rap_terms, filename = './output/5_terms-topterms-rapporteur.png', width = 4000, height=2000, units = 'px')

# interactive plot
p5_top_rap_terms_plotly <- ggplot(data=term.rap_top1, aes(x=count, y=rapporteur_fct, label=token, text=tooltip)) + 
    geom_bar(stat = "identity", position="stack") +
    labs(title='Most frequent nouns in non-AI paragraphs mentioning rapporteurs',
         x='Frequency', y='', 
         caption=paste0("\n", dataset_description, " Excluding rapporteur names")) + 
    theme_custom_rapp() +
    theme(plot.title.position='plot')

# save plotly
plotly::ggplotly(p5_top_rap_terms_plotly, tooltip="text") %>% 
  htmlwidgets::saveWidget(., file="./output/5a_terms-topterms-rapporteur.html")

rm(p5_top_rap_terms, rap.printnames, dataset_description, term.rap_top1, p5_top_rap_terms_plotly, theme_custom_rapp)
