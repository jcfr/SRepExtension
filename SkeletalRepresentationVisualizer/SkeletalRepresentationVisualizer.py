import vtk, qt, ctk, slicer
import os
import logging
import math
import xml.etree.ElementTree as ET
from slicer.ScriptedLoadableModule import (ScriptedLoadableModule, ScriptedLoadableModuleWidget,
                                           ScriptedLoadableModuleLogic, ScriptedLoadableModuleTest)
from LegacyTransformer.legacyTransformer import legacyTransformer as transformer

#
# visualize new srep format
#

class SkeletalRepresentationVisualizer(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Skeletal Representation Visualizer"
        self.parent.categories = ["Skeleton, topology"]
        self.parent.dependencies = []
        self.parent.contributors = ["Junpyo Hong, Zhiyuan Liu, Pablo Hernandez-Cerdan"]
        self.parent.helpText = """
    Given an header.xml or a .m3d (legacy) file with a Skeletal Representation, visualize it.
    """
        self.parent.acknowledgementText = """
    This file was originally developed by Junpyo Hong, Zhiyuan Liu, and currently maintained by the SlicerSALT team.
"""  # replace with organization, grant and thanks.


#
# SkeletalRepresentationVisualizerWidget
#

class SkeletalRepresentationVisualizerWidget(ScriptedLoadableModuleWidget):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        # Instantiate and connect widgets ...

        # Input file

        # Text + Button invoking QFileDialog
        self.inputFileLayout = qt.QHBoxLayout()
        self.inputFileLabelHeader = qt.QLabel()
        self.inputFileLabelHeader.text = "Input File: "
        self.inputFileLabelFile = qt.QLabel()
        self.inputFileLabelFile.text = "Input header.xml or .m3d"
        self.inputFileButton = qt.QPushButton()
        self.inputFileButton.text = "Browse"
        self.inputFileLayout.addWidget(self.inputFileLabelHeader)
        self.inputFileLayout.addWidget(self.inputFileLabelFile)
        self.inputFileLayout.addWidget(self.inputFileButton)
        self.layout.addLayout(self.inputFileLayout)

        #
        # Parameters Area
        #
        self.parametersCollapsibleButton = ctk.ctkCollapsibleButton()
        self.parametersCollapsibleButton.collapsed = True
        self.parametersCollapsibleButton.text = "Parameters for legacy m3d format"
        self.layout.addWidget(self.parametersCollapsibleButton)

        # Layout within the dummy collapsible button
        parametersFormLayout = qt.QFormLayout(self.parametersCollapsibleButton)

        # set distance of fold curve from interior points
        self.distSlider = slicer.qMRMLSliderWidget()
        self.distSlider.setProperty('maximum', 0.6)
        self.distSlider.setProperty('minimum', 0.0)
        self.distSlider.setProperty('singleStep', 0.01)

        self.distSlider.setToolTip("Parameter used in transformation from legacy s-rep to new s-rep")
        parametersFormLayout.addRow("Set distance to expand fold curve", self.distSlider)

        self.outputFolderLayout = qt.QHBoxLayout()
        self.outputFolderLabelHeader = qt.QLabel()
        self.outputFolderLabelHeader.text = "Output folder: "
        self.outputFolderLabelFile = qt.QLabel()
        self.outputFolderLabelFile.text = "Folder to save the new xml format"
        self.outputFolderButton = qt.QPushButton()
        self.outputFolderButton.text = "Browse"
        self.outputFolderLayout.addWidget(self.outputFolderLabelHeader)
        self.outputFolderLayout.addWidget(self.outputFolderLabelFile)
        self.outputFolderLayout.addWidget(self.outputFolderButton)
        parametersFormLayout.addRow(self.outputFolderLayout)

        #
        # Apply Button
        #
        self.applyButton = qt.QPushButton("Visualize s-rep file")
        self.applyButton.toolTip = "Parse and visualize s-rep."
        self.layout.addWidget(self.applyButton)

        # Unused
        # self.boundarySurfaceRendering = qt.QCheckBox()
        # self.boundarySurfaceRendering.checked = 0
        # self.boundarySurfaceRendering.setToolTip("If checked, set the visibility of the boundary mesh")
        # self.layout.addWidget(self.boundarySurfaceRendering)

        # connections
        self.applyButton.connect('clicked(bool)', self.onApplyButton)
        self.inputFileButton.connect('clicked(bool)', self.onInputFileButtonClicked)
        self.outputFolderButton.connect('clicked(bool)', self.onOutputFolderButtonClicked)
        # Add vertical spacer
        self.layout.addStretch(1)

    def cleanup(self):
        pass

    def onInputFileButtonClicked(self):
        filename = qt.QFileDialog.getOpenFileName(
            self.parent,
            'Open File', '', 'Files (*.m3d *.xml)')
        if filename == '':
            return False

        # Show the filename in the label.
        self.inputFileLabelFile.text = filename

        if filename.endswith('.m3d'):
            self.parametersCollapsibleButton.collapsed = False
            self.distSlider.setEnabled(True)
            self.outputFolderButton.setEnabled(True)
        elif filename.endswith('.xml'):
            self.parametersCollapsibleButton.collapsed = True
            self.distSlider.setEnabled(False)
            self.outputFolderButton.setEnabled(False)
        else:
            logging.warning('Invalid input file')
            return False

    def onOutputFolderButtonClicked(self):
        foldername = qt.QFileDialog.getExistingDirectory(
            self.parent,
            'Select folder to save xml files', '', qt.QFileDialog.ShowDirsOnly)
        if foldername == '':
            return False

        # Show the filename in the label.
        self.outputFolderLabelFile.text = foldername

    def onApplyButton(self):
        logic = SkeletalRepresentationVisualizerLogic()
        # Unused
        # flag = self.boundarySurfaceRendering.checked
        filename = self.inputFileLabelFile.text
        dist = self.distSlider.value
        outputFolder = self.outputFolderLabelFile.text
        logic.run(filename, dist, outputFolder)


#
# SkeletalRepresentationVisualizerLogic
#

class SkeletalRepresentationVisualizerLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    # def computeIndex(self, i, j, numRows, numCols):
    #     atomIndex = numCols * i  + j
    #     numEndAtoms = 0
    #     numStdAtoms = 0

    def distance(self, p0, p1):
        return math.sqrt((p0[0] - p1[0]) ** 2 + (p0[1] - p1[1]) ** 2 + (p0[2] - p1[2]) ** 2)

    def visualizeNewSrep(self, filename):
        """ Parse header.xml file, create models from the data, and visualize it. """
        # 1. parse header file
        tree = ET.parse(filename)
        upFileName = ''
        crestFileName = ''
        downFileName = ''
        nCols = 0
        nRows = 0
        headerFolder = os.path.dirname(filename)
        for child in tree.getroot():
            if child.tag == 'upSpoke':
                if os.path.isabs(child.text):
                    upFileName = os.path.join(headerFolder, child.text)
                upFileName = os.path.join(headerFolder, child.text)
            elif child.tag == 'downSpoke':
                downFileName = os.path.join(headerFolder, child.text)
            elif child.tag == 'crestSpoke':
                crestFileName = os.path.join(headerFolder, child.text)
            elif child.tag == 'nRows':
                nRows = (int)(child.text)
            elif child.tag == 'nCols':
                nCols = (int)(child.text)

        logging.info("upSpoke file: " + upFileName)
        logging.info("downSpoke file: " + downFileName)
        logging.info("crestSpoke file: " + crestFileName)

        reader = vtk.vtkXMLPolyDataReader()
        reader.SetFileName(upFileName)
        reader.Update()

        upSpokes = reader.GetOutput()

        upPointData = upSpokes.GetPointData()
        numberOfArrays = upPointData.GetNumberOfArrays()
        if numberOfArrays is 0:
            logging.warning("File: " + upFileName + " does not contain data")

        # medial_polyData = upSpokes #  this is poly data for skeleton

        scene = slicer.mrmlScene

        # base line of medial sheet
        fidDisplayNode = slicer.vtkMRMLMarkupsDisplayNode()
        scene.AddNode(fidDisplayNode)
        fidNode = slicer.vtkMRMLMarkupsFiducialNode()
        # If we would have more than 100 fiducial points (meant for editing points) better to use a regular MRMLModelNode
        # In the future, we would like the user to be able to move the nodes, and the connected structures to update accordingly.
        # Meanwhile, we lock the moving.
        fidNode.SetLocked(True)
        fidDisplayNode.SetGlyphScale(0.01)
        fidDisplayNode.SetSelectedColor(1.0, 1.0, 0.0)
        fidDisplayNode.SetTextScale(0.0)
        scene.AddNode(fidNode)
        fidNode.SetAndObserveDisplayNodeID(fidDisplayNode.GetID())
        # \TODO come up with better name later

        # prepare for arrows for upspokes
        upSpoke_points = vtk.vtkPoints()
        upSpoke_lines = vtk.vtkCellArray()

        arr_length = upPointData.GetArray('spokeLength')
        arr_dirs = upPointData.GetArray('spokeDirection')
        for i in range(upSpokes.GetNumberOfPoints()):
            pt = [0] * 3
            upSpokes.GetPoint(i, pt)
            # base point of up arrows
            id0 = upSpoke_points.InsertNextPoint(pt)

            # head of up arrows
            spoke_length = arr_length.GetValue(i)
            baseIdx = i * 3
            dirX = arr_dirs.GetValue(baseIdx)
            dirY = arr_dirs.GetValue(baseIdx + 1)
            dirZ = arr_dirs.GetValue(baseIdx + 2)
            pt1 = [0] * 3
            pt1[0] = pt[0] + spoke_length * dirX
            pt1[1] = pt[1] + spoke_length * dirY
            pt1[2] = pt[2] + spoke_length * dirZ
            id1 = upSpoke_points.InsertNextPoint(pt1)

            up_arrow = vtk.vtkLine()
            up_arrow.GetPointIds().SetId(0, id0)
            up_arrow.GetPointIds().SetId(1, id1)
            upSpoke_lines.InsertNextCell(up_arrow)

            fidNode.AddFiducial(pt[0], pt[1], pt[2])

        # boundary_point_ids = []

        # model node for medial mesh
        medial_model = slicer.vtkMRMLModelNode()
        medial_model.SetScene(scene)
        medial_model.SetName("Medial Mesh")
        medial_model.SetAndObservePolyData(reader.GetOutput())
        # model display node for the medial mesh
        medial_model_display = slicer.vtkMRMLModelDisplayNode()
        medial_model_display.SetColor(0, 0.5, 0)
        medial_model_display.SetScene(scene)
        medial_model_display.SetLineWidth(3.0)
        medial_model_display.SetRepresentation(1)
        medial_model_display.SetBackfaceCulling(0)
        scene.AddNode(medial_model_display)
        medial_model.SetAndObserveDisplayNodeID(medial_model_display.GetID())
        scene.AddNode(medial_model)

        # model node for up spoke (poly data for arrows)
        upSpoke_polyData = vtk.vtkPolyData()
        upSpoke_polyData.SetPoints(upSpoke_points)
        upSpoke_polyData.SetLines(upSpoke_lines)

        upSpoke_model = slicer.vtkMRMLModelNode()
        upSpoke_model.SetScene(scene)
        upSpoke_model.SetName("Top Spoke")
        upSpoke_model.SetAndObservePolyData(upSpoke_polyData)
        # model display node for the top spoke
        # cyan for the top spoke
        upSpoke_model_display = slicer.vtkMRMLModelDisplayNode()
        upSpoke_model_display.SetColor(0, 1, 1)
        upSpoke_model_display.SetScene(scene)
        upSpoke_model_display.SetLineWidth(3.0)
        upSpoke_model_display.SetBackfaceCulling(0)
        scene.AddNode(upSpoke_model_display)
        upSpoke_model.SetAndObserveDisplayNodeID(upSpoke_model_display.GetID())
        scene.AddNode(upSpoke_model)

        # prepare for down spokes
        reader.SetFileName(downFileName)
        reader.Update()
        downSpokes = reader.GetOutput()

        downSpoke_polyData = vtk.vtkPolyData()
        downSpoke_lines = vtk.vtkCellArray()
        downSpoke_points = vtk.vtkPoints()

        downPointData = downSpokes.GetPointData()
        arr_length = downPointData.GetArray('spokeLength')
        arr_dirs = downPointData.GetArray('spokeDirection')
        for i in range(downSpokes.GetNumberOfPoints()):
            # tail of arrows
            pt_tail = [0] * 3
            downSpokes.GetPoint(i, pt_tail)
            id0 = downSpoke_points.InsertNextPoint(pt_tail)

            # head of arrows
            pt_head = [0] * 3
            spoke_length = arr_length.GetValue(i)
            baseIdx = i * 3
            dirX = arr_dirs.GetValue(baseIdx)
            dirY = arr_dirs.GetValue(baseIdx+1)
            dirZ = arr_dirs.GetValue(baseIdx+2)
            pt_head[0] = pt_tail[0] + spoke_length * dirX
            pt_head[1] = pt_tail[1] + spoke_length * dirY
            pt_head[2] = pt_tail[2] + spoke_length * dirZ
            id1 = downSpoke_points.InsertNextPoint(pt_head)

            # connection between head and tail
            con = vtk.vtkLine()
            con.GetPointIds().SetId(0, id0)
            con.GetPointIds().SetId(1, id1)
            downSpoke_lines.InsertNextCell(con)

        downSpoke_polyData.SetPoints(downSpoke_points)
        downSpoke_polyData.SetLines(downSpoke_lines)

        downSpoke_model = slicer.vtkMRMLModelNode()
        downSpoke_model.SetScene(scene)
        downSpoke_model.SetName("Bottom Spoke")
        downSpoke_model.SetAndObservePolyData(downSpoke_polyData)
        # model display node for the down spoke
        downSpoke_model_display = slicer.vtkMRMLModelDisplayNode()
        downSpoke_model_display.SetColor(1, 0, 1)
        downSpoke_model_display.SetScene(scene)
        downSpoke_model_display.SetLineWidth(3.0)
        downSpoke_model_display.SetBackfaceCulling(0)
        scene.AddNode(downSpoke_model_display)
        downSpoke_model.SetAndObserveDisplayNodeID(downSpoke_model_display.GetID())
        scene.AddNode(downSpoke_model)

        # crest spoke
        new_reader = vtk.vtkXMLPolyDataReader()
        new_reader.SetFileName(crestFileName)
        new_reader.Update()
        foldCurve_polyData = new_reader.GetOutput()
        foldPointData = foldCurve_polyData.GetPointData()
        arr_length = foldPointData.GetArray('spokeLength')
        arr_dirs = foldPointData.GetArray('spokeDirection')
        crest_arrows_polydata = vtk.vtkPolyData()
        crest_arrows_points = vtk.vtkPoints()
        crest_arrows_lines = vtk.vtkCellArray()
        for i in range(foldCurve_polyData.GetNumberOfPoints()):
            # tail of crest arrows
            pt_tail = [0] * 3
            foldCurve_polyData.GetPoint(i, pt_tail)
            id0 = crest_arrows_points.InsertNextPoint(pt_tail)

            # head of crest arrows
            pt_head = [0] * 3
            spoke_length = arr_length.GetValue(i)
            baseIdx = i * 3
            dirX = arr_dirs.GetValue(baseIdx)
            dirY = arr_dirs.GetValue(baseIdx + 1)
            dirZ = arr_dirs.GetValue(baseIdx + 2)
            pt_head[0] = pt_tail[0] + spoke_length * dirX
            pt_head[1] = pt_tail[1] + spoke_length * dirY
            pt_head[2] = pt_tail[2] + spoke_length * dirZ
            id1 = crest_arrows_points.InsertNextPoint(pt_head)

            crest_line = vtk.vtkLine()
            crest_line.GetPointIds().SetId(0, id0)
            crest_line.GetPointIds().SetId(1, id1)
            crest_arrows_lines.InsertNextCell(crest_line)

        crest_arrows_polydata.SetPoints(crest_arrows_points)
        crest_arrows_polydata.SetLines(crest_arrows_lines)

        # show crest arrows
        crestSpoke_model = slicer.vtkMRMLModelNode()
        crestSpoke_model.SetScene(scene)
        crestSpoke_model.SetName("Crest Spoke")
        crestSpoke_model.SetAndObservePolyData(crest_arrows_polydata)
        # model display node
        crestSpoke_model_display = slicer.vtkMRMLModelDisplayNode()
        crestSpoke_model_display.SetColor(1, 1, 0)
        crestSpoke_model_display.SetScene(scene)
        crestSpoke_model_display.SetLineWidth(3.0)
        crestSpoke_model_display.SetBackfaceCulling(0)
        scene.AddNode(crestSpoke_model_display)
        crestSpoke_model.SetAndObserveDisplayNodeID(crestSpoke_model_display.GetID())
        scene.AddNode(crestSpoke_model)

        # show fold curve
        foldCurve_model = slicer.vtkMRMLModelNode()
        foldCurve_model.SetScene(scene)
        foldCurve_model.SetName("Fold Curve")
        foldCurve_model.SetAndObservePolyData(foldCurve_polyData)
        # model display node
        foldCurve_model_display = slicer.vtkMRMLModelDisplayNode()
        foldCurve_model_display.SetColor(1, 1, 0)
        foldCurve_model_display.SetScene(scene)
        foldCurve_model_display.SetLineWidth(3.0)
        foldCurve_model_display.SetBackfaceCulling(0)
        scene.AddNode(foldCurve_model_display)
        foldCurve_model.SetAndObserveDisplayNodeID(foldCurve_model_display.GetID())
        scene.AddNode(foldCurve_model)

        # show connections to fold curve point from nearby interior points
        # compute the nearest interior point
        connection_polydata = vtk.vtkPolyData()
        connection_points = vtk.vtkPoints()
        connection_lines = vtk.vtkCellArray()
        for i in range(foldCurve_polyData.GetNumberOfPoints()):
            min_dist = 100000.0
            nearest_index = 0
            pt_fold = [0] * 3
            foldCurve_polyData.GetPoint(i, pt_fold)
            id0 = connection_points.InsertNextPoint(pt_fold)

            for j in range(upSpokes.GetNumberOfPoints()):
                pt_interior = [0] * 3
                upSpokes.GetPoint(j, pt_interior)
                dist = self.distance(pt_fold, pt_interior)
                if dist < min_dist:
                    min_dist = dist
                    nearest_index = j

            pt_nearest_interior = upSpokes.GetPoint(nearest_index)
            id1 = connection_points.InsertNextPoint(pt_nearest_interior)
            line = vtk.vtkLine()

            line.GetPointIds().SetId(0, id0)
            line.GetPointIds().SetId(1, id1)

            connection_lines.InsertNextCell(line)

        connection_polydata.SetPoints(connection_points)
        connection_polydata.SetLines(connection_lines)
        connection_model = slicer.vtkMRMLModelNode()
        connection_model.SetScene(scene)
        connection_model.SetName("Connection to Fold Curve")
        connection_model.SetAndObservePolyData(connection_polydata)
        # model display node
        connection_model_display = slicer.vtkMRMLModelDisplayNode()
        connection_model_display.SetColor(0, 0, 0)
        connection_model_display.SetScene(scene)
        connection_model_display.SetLineWidth(3.0)
        connection_model_display.SetBackfaceCulling(0)
        scene.AddNode(connection_model_display)
        connection_model.SetAndObserveDisplayNodeID(connection_model_display.GetID())
        scene.AddNode(connection_model)

    def validateInputs(self, filename, dist, outputFolder):
        if os.path.exists(filename) is False:
            logging.error('Input filename: ' + filename + ' does not exist. Choose a valid filename.')
            return False

        if filename.endswith('.m3d'):
            logging.info('The input is a legacy s-rep')
            if os.path.isdir(outputFolder) is False:
                logging.error('OutputFolder: ' + outputFolder + ' . Please choose a valid folder to save the conversion to new xml format.')
                return False
            if dist > 0.0:
                return True
            else:
                logging.error('Legacy s-rep. Please set a positive distance in this case.')
                return False
        elif filename.endswith('.xml'):
            logging.info('The input is new s-rep')
            return True
        else:
            logging.error('Need legacy s-rep(*.m3d) or new s-rep files.')
            return False

    def run(self, filename, dist, outputFolder):

        """
        Run the actual algorithm
        """

        validInputs = self.validateInputs(filename, dist, outputFolder)
        if validInputs is False:
            logging.error('Invalid input parameters')
            return False

        logging.info('Processing started')
        if filename.endswith('.m3d'):
            newSrepFile = self.transformLegacySrep(filename, dist, outputFolder)
            self.visualizeNewSrep(newSrepFile)

        elif filename.endswith('.xml'):
            self.visualizeNewSrep(filename)
        logging.info('Processing completed')
        return True

    def transformLegacySrep(self, filename, dist, outputFolder):
        logging.info('The input is legacy s-rep, now converting to new s-rep')
        transformer().transformLegacySrep(filename, outputFolder, dist)
        return os.path.join(outputFolder, 'header.xml')


class SkeletalRepresentationVisualizerTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
        """
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        """Run as few or as many tests as needed here.
        """
        self.setUp()
        self.test_SkeletalRepresentationVisualizer1()

    def test_SkeletalRepresentationVisualizer1(self):
        """ Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")
        #
        # first, get some data
        #
        volumeNode = slicer.util.getNode(pattern="FA")
        logic = SkeletalRepresentationVisualizerLogic()
        self.assertIsNotNone(logic.hasImageData(volumeNode))
        self.delayDisplay('Test passed!')
