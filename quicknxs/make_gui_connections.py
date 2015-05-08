from plot2d_dialog_refl import Plot2dDialogREFL

class MakeGuiConnections(object):
    
    def __init__(cls, self):

        self.ui.data_yt_plot.singleClick.connect(self.single_click_data_yt_plot)
        self.ui.data_yt_plot.leaveFigure.connect(self.leave_figure_yt_plot)
        self.ui.data_yt_plot.logtogy.connect(self.logy_toggle_yt_plot)
        self.ui.data_yt_plot.toolbar.homeClicked.connect(self.home_clicked_yt_plot)
        self.ui.data_yt_plot.toolbar.exportClicked.connect(self.export_yt)
    
        self.ui.norm_yt_plot.singleClick.connect(self.single_click_norm_yt_plot)
        self.ui.norm_yt_plot.leaveFigure.connect(self.leave_figure_yt_plot)
        self.ui.norm_yt_plot.logtogy.connect(self.logy_toggle_yt_plot)
        self.ui.norm_yt_plot.toolbar.homeClicked.connect(self.home_clicked_yt_plot)
        self.ui.norm_yt_plot.toolbar.exportClicked.connect(self.export_yt)
    
        self.ui.data_yi_plot.singleClick.connect(self.single_click_data_yi_plot)
        self.ui.data_yi_plot.leaveFigure.connect(self.leave_figure_yi_plot)
        self.ui.data_yi_plot.logtogx.connect(self.logx_toggle_yi_plot)
        self.ui.data_yi_plot.toolbar.homeClicked.connect(self.home_clicked_yi_plot)
        self.ui.data_yi_plot.toolbar.exportClicked.connect(self.export_yi)
    
        self.ui.norm_yi_plot.singleClick.connect(self.single_click_norm_yi_plot)
        self.ui.norm_yi_plot.leaveFigure.connect(self.leave_figure_yi_plot)
        self.ui.norm_yi_plot.logtogx.connect(self.logx_toggle_yi_plot)
        self.ui.norm_yi_plot.toolbar.homeClicked.connect(self.home_clicked_yi_plot)
        self.ui.norm_yi_plot.toolbar.exportClicked.connect(self.export_yi)
        
        self.ui.data_it_plot.singleClick.connect(self.single_click_data_it_plot)
        self.ui.data_it_plot.leaveFigure.connect(self.leave_figure_it_plot)
        self.ui.data_it_plot.logtogy.connect(self.logy_toggle_it_plot)
        self.ui.data_it_plot.toolbar.homeClicked.connect(self.home_clicked_it_plot)
        self.ui.data_it_plot.toolbar.exportClicked.connect(self.export_it)
    
        self.ui.norm_it_plot.singleClick.connect(self.single_click_norm_it_plot)
        self.ui.norm_it_plot.leaveFigure.connect(self.leave_figure_it_plot)
        self.ui.norm_it_plot.logtogy.connect(self.logy_toggle_it_plot)
        self.ui.norm_it_plot.toolbar.homeClicked.connect(self.home_clicked_it_plot)
        self.ui.norm_it_plot.toolbar.exportClicked.connect(self.export_it)
    
        self.ui.data_ix_plot.singleClick.connect(self.single_click_data_ix_plot)
        self.ui.data_ix_plot.leaveFigure.connect(self.leave_figure_ix_plot)
        self.ui.data_ix_plot.logtogy.connect(self.logy_toggle_ix_plot)
        self.ui.data_ix_plot.toolbar.homeClicked.connect(self.home_clicked_ix_plot)
        self.ui.data_ix_plot.toolbar.exportClicked.connect(self.export_ix)
    
        self.ui.norm_ix_plot.singleClick.connect(self.single_click_norm_ix_plot)
        self.ui.norm_ix_plot.leaveFigure.connect(self.leave_figure_ix_plot)
        self.ui.norm_ix_plot.logtogy.connect(self.logy_toggle_ix_plot)
        self.ui.norm_ix_plot.toolbar.homeClicked.connect(self.home_clicked_ix_plot)
        self.ui.norm_ix_plot.toolbar.exportClicked.connect(self.export_ix)
    
        self.ui.data_stitching_plot.singleClick.connect(self.single_click_data_stitching_plot)
        self.ui.data_stitching_plot.leaveFigure.connect(self.leave_figure_data_stitching_plot)
        self.ui.data_stitching_plot.toolbar.homeClicked.connect(self.home_clicked_data_stitching_plot)
        self.ui.data_stitching_plot.logtogx.connect(self.logx_toggle_data_stitching)
        self.ui.data_stitching_plot.logtogy.connect(self.logy_toggle_data_stitching)
        self.ui.data_stitching_plot.toolbar.exportClicked.connect(self.export_stitching_data)
        
        self.fileLoaded.connect(self.updateLabels)
        self.fileLoaded.connect(self.plotActiveTab)
        #self.initiateProjectionPlot.connect(self.plot_projections)
        #self.initiateReflectivityPlot.connect(self.plot_refl)
        #self.initiateReflectivityPlot.connect(self.updateStateFile)
        
        for plot in [self.ui.data_yt_plot, 
                     self.ui.data_it_plot,
                     self.ui.data_yi_plot,
                     self.ui.data_ix_plot,
                     self.ui.norm_yt_plot, 
                     self.ui.norm_it_plot,
                     self.ui.norm_yi_plot,
                     self.ui.norm_ix_plot]:
            plot.canvas.mpl_connect('motion_notify_event', self.plotMouseEvent)
            
        #for plot in [self.ui.data_yt_plot, 
                     #self.ui.data_it_plot,
                     #self.ui.data_ix_plot,
                     #self.ui.norm_yt_plot, 
                         #self.ui.norm_it_plot,
                     #self.ui.norm_ix_plot]:
          #plot.canvas.mpl_connect('scroll_event', self.changeColorScale)
    
        self.ui.norm_yt_plot.canvas.mpl_connect('motion_notify_event', self.mouseNormPlotyt)
        self.ui.norm_yt_plot.canvas.mpl_connect('button_press_event', self.mouseNormPlotyt)
        self.ui.norm_yt_plot.canvas.mpl_connect('button_release_event', self.mouseNormPlotyt)
                