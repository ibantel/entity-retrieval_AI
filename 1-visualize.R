

library(tidyverse)
library(lubridate)

newsletters <- read_csv("./data/preprocessed/newsletters_preprocessed_backup.csv") %>% filter(mentioned >= 0) %>% filter(topic!="total")
rapporteurs <- read_csv("./data/preprocessed/rapporteurs_preprocessed_backup.csv") %>% select(-`...1`)

newsletters <- left_join(newsletters, rapporteurs, by=c('rapporteur'='lastname')) %>% select(-rapporteur) %>% rename(rapporteur=printname)

all_rapporteurs <- newsletters %>% select(rapporteur) %>% unique() %>% pull(rapporteur)

rapporteurs_order_raw <- newsletters %>% 
  filter(topic=="AI") %>% 
  select(rapporteur, mentioned) %>% 
  group_by(rapporteur) %>% 
  summarise(mentioned=sum(mentioned)) %>% 
  ungroup() %>% 
  arrange(mentioned) %>% 
  pull(rapporteur)

rapporteurs_order <- c(setdiff(all_rapporteurs, rapporteurs_order_raw), rapporteurs_order_raw)

newsletters_plot <- newsletters %>% 
  group_by(rapporteur, topic) %>% 
  summarize(mentioned = sum(mentioned), primary=first(primary), .groups = 'keep') %>% 
  ungroup() %>% 
  mutate(rapporteur = fct_relevel(rapporteur, rapporteurs_order),
         topic = fct_relevel(topic, 'nonAI', 'AI'))

p_rapporteurs_all <- ggplot(data = newsletters_plot,
                            aes(y=rapporteur, x=mentioned, fill=topic)) + 
  geom_bar(position = "stack", stat="identity") +
  scale_fill_grey(start=0.8, end=0.2, labels=c("nonAI" = "not related to AI act", "AI"="related to AI act")) + 
  ggtitle("Prevalence of rapporteurs, by type of mention") + 
  xlab("Number of mentions") + 
  ylab("") +
  labs(fill='Type of mention')  + 
  ggthemes::theme_base() + 
  theme(legend.position = "bottom",
        axis.text  = element_text(size=12),
        axis.title = element_text(size=16),
        plot.title = element_text(size=22),
        legend.title = element_text(size=16),
        legend.text = element_text(size=12)
  ) 

ggsave(p_rapporteurs_all, filename = "./output/1-all_rapporteurs_all_mentions.png", width = 2800, height = 1600, units = "px")


p_overtime_top5 <- newsletters %>% 
  filter(rapporteur %in% tail(rapporteurs_order, 5),
         topic=="AI") %>% 
  mutate(date_q = zoo::as.yearqtr(date),
         date_y = lubridate::year(date),
         rapporteur = fct_rev(rapporteur)) %>% 
  ggplot(data=., aes(x=date_q, y = mentioned, fill=rapporteur)) +
  geom_bar(stat = "identity", position="stack") +
  scale_fill_grey(start=0.8, end=0.2) +
  ggtitle("Top 5 rapporteurs' prevalence on AI act over time") + 
  xlab("Date") + 
  ylab("Number of AI act-related mentions") +
  labs(fill='Rapporteur')  + 
  #theme_minimal() + 
  ggthemes::theme_base() + 
  theme(legend.position = "right",
        axis.text  = element_text(size=12),
        axis.title = element_text(size=16),
        plot.title = element_text(size=22),
        legend.title = element_text(size=16),
        legend.text = element_text(size=12)
        ) 

ggsave(p_overtime_top5, filename = "./output/2-top5_AI_overtime.png", width = 2800, height = 1600, units = "px")
         