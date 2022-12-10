theme_custom_rapp <- function(){ 
  font <- "Times New Roman"   #assign font family up front
  
  theme_classic() %+replace%    #replace elements we want to change
    
    theme(
      
      plot.title.position = 'plot',  # plot title according to plot outer lines
      plot.caption.position = 'plot',
      
      #grid elements
      #panel.grid.major = element_blank(),    #strip major gridlines
      #panel.grid.minor = element_blank(),    #strip minor gridlines
      #axis.ticks = element_blank(),          #strip axis ticks
      
      #since theme_minimal() already strips axis lines, 
      #we don't need to do that again
      
      #text elements
      plot.title = element_text(             #title
        family = font,            #set font family
        size = 22,                #set font size
        face = 'bold',            #bold typeface
        hjust = 0,                #left align
        vjust = 2,               #raise slightly
        margin = margin(0,0,10,0)),
      
      plot.subtitle = element_text(          #subtitle
        family = font,            #font family
        size = 14),               #font size
      
      plot.caption = element_text(           #caption
        family = font,            #font family
        size = 9,                 #font size
        hjust = 1),               #right align
      
      axis.title = element_text(             #axis titles
        family = font,            #font family
        size = 16),               #font size
      
      axis.text = element_text(              #axis text
        family = font,            #axis family
        size = 12),                #font size
      
      axis.text.x = element_text(            #margin for axis text
        margin=margin(5, b = 10)),
      
      legend.title = element_text(
        family = font,
        size=16),
      
      legend.text = element_text(
        family = font,
        size = 12
      ),
      
      # facet_wrap
      strip.text = element_text(size=16), # size of facet_wrap labels
      strip.background = element_rect(# box
        color="white", # border color
        fill='white' # fill color
      )
      
      #since the legend often requires manual tweaking 
      #based on plot content, don't define it here
    )
}
